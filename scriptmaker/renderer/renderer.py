from __future__ import annotations

import json
import pkgutil
import re
import tempfile
import weasyprint

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from queue import SimpleQueue

import scriptmaker.constants as constants 
import scriptmaker.data as data
import scriptmaker.models as models
import scriptmaker.templates as templates 
import scriptmaker.utilities as utilities


class Renderer ():
    """ 
    A script-to-PDF renderer.
    """
      
    def render_script (
        self, script : models.Script, *,
        output_folder = None
    ):
        """
        Renders the script PDF, returning the path to the file.
        """
        script.finalize()
        
        output_folder = Path(output_folder, 'pdf') if output_folder else Path(script.data.workspace, "pdf")
        utilities.filesystem.mkdirp(output_folder.parent)
        utilities.filesystem.mkdirp(output_folder)
        
        # We are going to calculate some layouts, so we're gonna need a few numbers.
        ppi = 144.
        page_w, page_h = ppi * 8.5, ppi * 11. 
        page_padding = 0.02
        page_content = (1 - 2 * page_padding)
        header = 60.
        content_w, content_h = page_content * page_w, page_content * page_h - header
        column_gap = 0.02
        icon_size = 45.
        character_overflow = 15
        character_trailing = 30.
        character_w, character_h = (1. - column_gap) / 2. * content_w, icon_size + character_overflow
        jinx_w, jinx_h = content_w, 30.
        
        # Calculate the height of each section.
        heights = {}
        for team in constants.TEAMS:
            if team not in script.by_team: heights[team] = 0. 
            else:
                members = len(script.by_team[team])
                height = character_trailing + character_h * int((members + 1) / 2)
                heights[team] = height
        heights["jinxes"] = jinx_h * sum([ len(jinxes) for id, jinxes in script.jinxes.items() ])
        
        # Separate out teams into page groups (including jinxes as a team). Follow a cramming heuristic.
        to_add = SimpleQueue()
        for team in script.by_team:
            if len(script.by_team[team]) > 0:
                to_add.put(team)
    
        # If we want jinxes to flow, we should try to cram it too.
        if not script.options.force_jinxes:
            to_add.put('jinxes')
        
        page_groups = [{ "teams": [], "height": 0 }]
        
        while not to_add.empty():
            next_team = to_add.get()
            cumulative = page_groups[-1]['height']
            current_height = heights[next_team]
            # If the current page is empty, don't skip it just because the current group is too big.
            if cumulative == 0 or cumulative + current_height < content_h:
                page_groups[-1]['teams'].append(next_team)
                page_groups[-1]['height'] += current_height
            else:
                page_groups.append({ "teams": [next_team], "height": current_height })

        # If we always want jinxes on a new page
        if script.options.force_jinxes:
            page_groups.append({ "teams": ["jinxes"], "height": 0 })
        
        jinxes_next_page = len(page_groups[-1]["teams"]) == 1 or script.options.force_jinxes
        if jinxes_next_page:
            page_groups.pop()

        # Decide where we'll build icons.
        workspace = output_folder

        # Bold the ability text.
        abilities = {}
        for character in script.characters:
            abilities[character.id] = re.sub(r'(?P<setup>\[.*\])', '<b>\g<setup></b>', character.ability)

        # Calculate spacers for small team names.
        needs_spacers = { team: len(script.by_team[team]) == 1 for team in script.by_team }
        
        # Calculate spacers for large team names.
        for team in ['townsfolk', 'outsider', 'traveler']:
            needs_spacers[team] = len(script.by_team[team]) <= 2

        def num_spacers(team):
            match team:
                case 'townsfolk' | 'outsider' | 'traveler':
                    return 7
                case 'fabled':
                    return 4
                case _:
                    return 5

        spacers = { team: num_spacers(team) for team in needs_spacers if needs_spacers[team] is True }

        for team in ['townsfolk', 'outsider', 'traveler']:
            if len(script.by_team[team]) == 2:
                spacers[team] = 1

        # Pass configuration forwards to jinja/weasyprint stack.  
        params = {
            "pages": [ group['teams'] for group in page_groups ],
            "characters": { character.id: character for character in script.characters },
            "abilities": abilities,
            "spacers": spacers,
            "teams": script.by_team,
            "icons": { id: f"file://{icon.path(Path(workspace.parent, 'build', 'icons').resolve())}" for id, icon in script.data.icons.items() },
            "logo": f"file://{script.meta.icon.path(Path(workspace.parent, 'build').resolve())}" if script.meta.icon else "",
            "jinxes": script.jinxes,
            "has_jinxes": sum([ len(jinxes) for id, jinxes in script.jinxes.items() ]) > 0,
            "jinxes_next_page": jinxes_next_page,
            "meta": script.meta,
            "options": script.options
        }
        output_path = Path(output_folder, f"{utilities.sanitize.name(script.meta.name)}-script.pdf")  
        
        return self.__render_jinja(
            workspace = workspace,
            template = "script.jinja",
            style = "script.css",
            icons = script.data.icons.values(),
            logo = script.meta.icon,
            params = params,
            output_file = output_path
        )
        
        
    def render_nightorder (
        self, script : models.Script, *, 
        output_folder = None
    ):
        """
        Renders the nightorder PDF, returning the file path.
        """
        script.finalize()
        
        output_folder = Path(output_folder, 'pdf') if output_folder else Path(script.data.workspace, "pdf")
        utilities.filesystem.mkdirp(output_folder.parent)
        utilities.filesystem.mkdirp(output_folder)
        
        workspace = output_folder
        
        # Pass configuration forwards to jinja/weasyprint stack.  
        params = {
            
            "characters": { character.id: character for character in script.characters },
            "icons": { id: f"file://{icon.path(Path(workspace.parent, 'build', 'icons').resolve())}" for id, icon in script.data.icons.items() },
            "logo": f"file://{script.meta.icon.path(Path(workspace.parent, 'build').resolve())}" if script.meta.icon else "",
            "nightorder": script.nightorder,
            "meta": script.meta,
            "options": script.options
        }
        
        nights_style = 'nights-simple' if script.options.simple_nightorder else 'nights-full'
        output_path = Path(output_folder, f"{utilities.sanitize.name(script.meta.name)}-{nights_style}.pdf")
        
        return self.__render_jinja(
            workspace = workspace,
            template = "nights.jinja",
            style = "nights.css",
            icons = script.data.icons.values(),
            logo = script.meta.icon,
            params = params,
            output_file = output_path
        )
    
    
    def __render_jinja (self, *, workspace, template, style, icons, logo, params, output_file):
        """
        Renders a jinja template (in the templates directory) and converts to PDF.
        """
        tmpdir = Path(workspace.parent, 'build')
        utilities.filesystem.mkdirp(tmpdir)
        
        # Load the jinja templates, CSS and fonts into our tmpdir, so we can pretend it's an environment.
        for file in templates.COMMON + [template, style]:
            file_content = templates.get_data(file)
            with open(Path(tmpdir, file), "wb") as tmpfile:
                tmpfile.write(file_content)
        
        # Load the icons so the script can reference them.
        utilities.filesystem.mkdirp(Path(tmpdir, 'icons'))
        for icon in icons:
            icon.save(Path(tmpdir, 'icons'))
        
        # Save the logo.
        if logo:
            logo.save(tmpdir)
        
        # Process the corresponding jinja template.
        loader = FileSystemLoader(tmpdir)
        env = Environment(loader = loader, extensions=['jinja2.ext.loopcontrols'])
        html = env.get_template(template).render(params)
        
        # Save the HTML for build introspection.
        with open(Path(tmpdir, output_file.stem).with_suffix('.html'), 'w') as html_file:
            html_file.write(html)
        
        # Make sure there's an output directory.
        utilities.filesystem.mkdirp(Path(output_file).parent)
        
        # Render the HTML out as full-quality PDF to the given location.
        weasyprint.HTML(string = html).write_pdf(
            target = output_file,
            stylesheets = [Path(tmpdir, style), Path(tmpdir, "common.css")],
            jpeg_quality = 95,
            full_fonts = True
        )
        
        return output_file