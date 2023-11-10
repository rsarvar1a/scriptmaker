from __future__ import annotations

import json
import pkgutil
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
    
    def render (
        self, script : models.Script, *, 
        output_folder = None
    ):
        """ 
        Renders the given script into PDFs. 
        """
        script.finalize()
        
        folder = output_folder if output_folder else Path(script.data.workspace, "pdf")
        script_path = self.__render_script(script, output_folder = folder)
        nightorder_path = self.__render_nightorder(script, output_folder = folder)
        
        return {
            "script": script_path,
            "nightorder": nightorder_path
        }
    
    
    def __render_script (
        self, script : models.Script, *,
        output_folder = None
    ):
        """
        Renders the script PDF, returning the path to the file.
        """
        
        # We are going to calculate some layouts, so we're gonna need a few numbers.
        ppi = 200.
        page_w, page_h = ppi * 8.5, ppi * 11. 
        page_padding = 0.02
        page_content = (1 - 2 * page_padding)
        header = 70.
        content_w, content_h = page_content * page_w, page_content * page_h - header
        column_gap = 0.02
        icon_size = 45.
        character_overflow = 15
        character_trailing = 65.
        character_w, character_h = (1. - column_gap) / 2. * content_w, icon_size + character_overflow
        jinx_w, jinx_h = content_w, 30.
        
        # Calculate the height of each section.
        heights = {}
        for team in constants.TEAMS:
            if team not in script.by_team: heights[team] = 0. 
            else:
                members = len(script.by_team[team])
                height = character_trailing + character_h * (members + 1) / 2
                heights[team] = height
        heights["jinxes"] = jinx_h * len(script.jinxes)
        
        # Separate out teams into page groups (including jinxes as a team). Follow a cramming heuristic.
        to_add = SimpleQueue()
        for team in script.by_team:
            if len(script.by_team[team]) > 0:
                to_add.put(team)
        
        page_groups = [{ "teams": [], "height": 0 }]
        
        while not to_add.empty():
            next_team = to_add.get()
            cumulative = page_groups[-1]['height']
            current_height = heights[next_team]
            if cumulative + current_height < content_h:
                page_groups[-1]['teams'].append(next_team)
                page_groups[-1]['height'] += current_height
            else:
                page_groups.append({ "teams": [next_team], "height": current_height })

        # Decide where we'll build icons.
        workspace = script.data.workspace

        # Pass configuration forwards to jinja/weasyprint stack.  
        params = {
            "pages": [ group['teams'] for group in page_groups ],
            "characters": { character.id: character for character in script.characters },
            "spacers": { team: len(script.by_team[team]) == 1 for team in script.by_team },
            "teams": script.by_team,
            "icons": { id: f"file://{icon.path(Path(workspace, 'build', 'icons').resolve())}" for id, icon in script.data.icons.items() },
            "logo": f"file://{script.meta.icon.path(Path(workspace, 'build').resolve())}" if script.meta.icon else "",
            "jinxes": script.jinxes,
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
        
        
    def __render_nightorder (
        self, script : models.Script, *, 
        output_folder = None
    ):
        """
        Renders the nightorder PDF, returning the file path.
        """
        workspace = script.data.workspace
        
        # Pass configuration forwards to jinja/weasyprint stack.  
        params = {
            
            "characters": { character.id: character for character in script.characters },
            "icons": { id: f"file://{icon.path(Path(workspace, 'build', 'icons').resolve())}" for id, icon in script.data.icons.items() },
            "logo": f"file://{script.meta.icon.path(Path(workspace, 'build').resolve())}" if script.meta.icon else "",
            "nightorder": script.nightorder,
            "meta": script.meta,
            "options": script.options
        }
        output_path = Path(output_folder, f"{utilities.sanitize.name(script.meta.name)}-nights.pdf")
        
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
        tmpdir = Path(workspace, 'build')
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