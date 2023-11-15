from __future__ import annotations

import drawsvg
import re
import weasyprint

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

import scriptmaker.data as data
import scriptmaker.models as models
import scriptmaker.templates as templates 
import scriptmaker.utilities as utilities


class Tokenizer ():
    """ 
    Lays out tokens in a datastore for physical printing.
    """
    
    def render (
        self, datastore : data.Datastore, *,
        name, 
        characters = [],
        character_copies = {},
        output_folder = None,
        render_everything = False,
        character_token_size = 45, 
        reminder_token_size = 19
    ):
        """
        Renders a script's (or it's datastore's) entire token set into a physically-printable layout.
        """
        # What are we rendering, and to where?
        folder = Path(output_folder, 'pdf') if output_folder else Path(datastore.workspace, "pdf")
        utilities.filesystem.mkdirp(folder)
                
        tmpdir = Path(folder.parent, 'build')
        utilities.filesystem.mkdirp(tmpdir)
        
        output_path = Path(folder, f"{utilities.sanitize.name(name)}-tokens.pdf")
        
        # Build a parameter set for each character we want to print.
        character_set = datastore.characters.values() if render_everything else [datastore.characters[id] for id in characters]
        
        character_tokens = []
        reminder_tokens = []
        
        # Create the stupid name SVGs in here because Weasyprint sucks...
        class CharacterToken ():
            def __init__ (self, *, id, name, ability, icon, setup, first, other, reminders, out):
                self.id = id; self.name = name.upper(); self.ability = ability; self.icon = icon
                self.setup = setup; self.first = first; self.other = other; self.reminders = reminders
                self.ability = re.sub(r'(?P<setup>\[.*\])', '<b>\g<setup></b>', self.ability)
                self.fontsize = "-large" if len(self.ability) >= 125 else ""
                d = drawsvg.Drawing(500, 500)
                p = drawsvg.Path(fill='transparent')
                p.M(75, 250)
                p.A(175, 175, 0, 0, 0, 425, 250)
                d.append(p)
                t = drawsvg.Text(self.name, 60, path = p, fill='black', text_anchor = 'middle', center = True, font_family = 'Dumbledor 1')
                d.append(t)
                self.name = Path(out, f"{self.id}.png").resolve()
                d.set_pixel_scale(2)
                d.save_png(str(self.name)) 
                self.name = f"file://{self.name}"      


        class ReminderToken ():
            def __init__ (self, *, id, icon, text, out):
                self.id = id; self.icon = icon; self.text = text
                d = drawsvg.Drawing(500, 500)
                p = drawsvg.Path(fill='transparent')
                p.M(75, 250)
                p.A(175, 175, 0, 0, 0, 425, 250)
                d.append(p)
                t = drawsvg.Text(self.text, 70, path = p, fill='white', text_anchor = 'middle', center = True, font_family = 'Dumbledor 1')
                d.append(t)
                self.text = Path(out, f"{self.id}.png").resolve()
                d.set_pixel_scale(2)
                d.save_png(str(self.text))
                self.text = f"file://{self.text}"
        
        
        text_svg_folder = Path(tmpdir, 'svgs').resolve()
        utilities.filesystem.mkdirp(text_svg_folder)

        for character in character_set:
            if character.team == '_meta': continue
            
            reminder_count = len(character.reminders + character.remindersGlobal)
            character_entry = CharacterToken(
                id = character.id,
                name = character.name, ability = character.ability,
                icon = f"file://{datastore.icons[character.id].path(Path(tmpdir, 'icons').resolve())}",
                setup = f"file://{Path(tmpdir,'leaf-setup.png').resolve()}" if character.setup else None,
                first = f"file://{Path(tmpdir,'leaf-first.png').resolve()}" if character.nightinfo['first']['acts'] else None,
                other = f"file://{Path(tmpdir,'leaf-other.png').resolve()}" if character.nightinfo['other']['acts'] else None,
                reminders = f"file://{Path(tmpdir, f'leaf-reminder-{min(reminder_count, 7)}.png').resolve()}" if reminder_count > 0 else None,
                out = text_svg_folder
            )
            if character.id in character_copies:
                character_tokens.extend([character_entry] * character_copies[character.id])
            else:
                character_tokens.append(character_entry)
            for i, reminder_text in enumerate(character.reminders + character.remindersGlobal):
                reminder_entry = ReminderToken(
                    id = f"{character.id}-{i}",
                    icon = character_entry.icon,
                    text = reminder_text,
                    out = text_svg_folder
                )
                reminder_tokens.append(reminder_entry)
                
        # Set up all other params.
        token_path = f"file://{Path(tmpdir, 'token.png').resolve()}"

        params = {
            "characters": character_tokens,
            "reminders": reminder_tokens,
            "token_background": token_path,
            "character_size": f"{character_token_size}mm",
            "reminder_size": f"{reminder_token_size}mm"
        }
        
        # Load every asset we need into the build workspace.
        for file in templates.COMMON + ['tokens.jinja', 'tokens.css']:
            file_content = templates.get_data(file)
            with open(Path(tmpdir, file), "wb") as tmpfile:
                tmpfile.write(file_content)
        
        for file in templates.tokens.COMMON:
            file_content = templates.tokens.get_data(file)
            with open(Path(tmpdir, file), 'wb') as tmpfile:
                tmpfile.write(file_content)
        
        utilities.filesystem.mkdirp(Path(tmpdir, 'icons'))
        for character in character_set:
            cropped = datastore.icons[character.id].crop()
            cropped.save(Path(tmpdir, 'icons'))
        
        # Render everything and save.
        loader = FileSystemLoader(tmpdir)
        env = Environment(loader = loader, extensions=['jinja2.ext.loopcontrols'])
        html = env.get_template('tokens.jinja').render(params)
        
        with open(Path(tmpdir, output_path.stem).with_suffix('.html'), 'w') as html_file:
            html_file.write(html)
            
        utilities.filesystem.mkdirp(Path(output_path).parent)
        
        weasyprint.HTML(string = html).write_pdf(
            target = output_path,
            stylesheets = [Path(tmpdir, 'tokens.css'), Path(tmpdir, 'common.css')],
            jpeg_quality = 95,
            full_fonts = True
        )
        
        return output_path