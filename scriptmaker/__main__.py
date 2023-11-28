
import argparse 
import io
import json
import sys
import traceback
import urllib.request
   
from pathlib import Path 
   
from scriptmaker import Datastore, PDFTools, Renderer, Script, ScriptmakerError, Tokenizer, utilities


def main ():

    # Delegate out to the respective CLI.

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser.set_defaults(func = fourohfour)

    # scriptmaker make-pdf 
    # (--script SCRIPT | --url URL | --recurse DIRECTORY) 
    # [--output-folder OUTPUT]
    # [--nights]
    # [--simple-nightorder]
    # [--i18n-fallback]
    # [--postprocess]

    makepdfs = subparsers.add_parser('make-pdf')
    makepdfs.add_argument('--output-folder')
    inputs = makepdfs.add_argument_group('inputs')
    source = inputs.add_mutually_exclusive_group(required = True)
    source.add_argument('--recurse')
    source.add_argument('--script')
    source.add_argument('--url')
    inputs.add_argument('--nights')
    styles = makepdfs.add_argument_group('styles')
    styles.add_argument('--bucket', action = 'store_true')
    styles.add_argument('--full', action = 'store_true')
    styles.add_argument('--simple', action = 'store_true')
    options = makepdfs.add_argument_group('options')
    options.add_argument('--i18n-fallback', action = 'store_true')
    options.add_argument('--postprocess', action = 'store_true')
    makepdfs.set_defaults(func = cmd_make_pdf)
    
    # scriptmaker tokenize
    # (directory DIRECTORY)
    # [--output-folder OUTPUT]
    # [--official-only | --exclude-official]
    # [--character-size SIZE]
    # [--reminder-size SIZE]
    # [--extra-copies FILE]
    # [--postprocess]

    tokenize = subparsers.add_parser('tokenize')
    tokenize.add_argument('directory')
    tokenize.add_argument('--output-folder')
    official = tokenize.add_mutually_exclusive_group(required = False)
    official.add_argument('--official-only', action = 'store_true')
    official.add_argument('--exclude-official', action = 'store_true')
    options = tokenize.add_argument_group('options')
    options.add_argument('--character-size')
    options.add_argument('--reminder-size')
    options.add_argument('--extra-copies')
    options.add_argument('--postprocess', action = 'store_true')
    tokenize.set_defaults(func = cmd_tokenize)

    # Fire
    
    args = parser.parse_args()
    args.func(args)


def fourohfour (args):
    print('usage: scriptmaker (make-pdf | tokenize)')
    exit(1)


def cmd_make_pdf (args):
    
    if args.recurse:     
        if not args.output_folder:
            args.output_folder = Path(args.recurse)
        utilities.filesystem.mkdirp(args.output_folder)
        datastore = Datastore(args.output_folder)
        datastore.add_official_characters()
           
        for json_path in sorted(Path(args.recurse).resolve().rglob("*.json")):
            try:
                with open(json_path) as json_file:
                    script_json = json.load(json_file)

                if not isinstance (script_json, list) or len(script_json) == 0:
                    continue

                output_folder = json_path.parent
                script : Script = datastore.load_script(script_json)
                
                if args.i18n_fallback:
                    script.options.i18n_fallback = True

                results = set()

                if args.bucket:
                    script.options.bucket = True

                path = Renderer().render_script(script, output_folder = output_folder)
                results.add(path)

                if args.full:
                    script.options.simple_nightorder = False
                    path = Renderer().render_nightorder(script, output_folder = output_folder)
                    results.add(path)
                    
                if args.simple:
                    script.options.simple_nightorder = True
                    paths = Renderer().render_nightorder(script, output_folder = output_folder)
                    results.add(paths)

                if args.postprocess:
                    for path in results:
                        PDFTools.compress(path)
                        PDFTools.pngify(path)
                
                for path in results:
                    print(str(path))        
                
            except (ScriptmakerError, TypeError, Exception):
                print(traceback.format_exc())
                continue
    
    else:    
        try:
            if args.script:
                with open(args.script) as json_file:
                    script_json = json.load(json_file)
                    path = Path(args.script).parent
            elif args.url:
                buffer = io.BytesIO()
                urllib.request.urlretrieve(args.url, buffer)
                script_json = json.load(buffer)
                path = '.'
            
            if args.nights:
                with open(args.nights) as nights_file:
                    nights_json = json.load(nights_file)
            else:
                nights_json = None
            
            if not args.output_folder:
                args.output_folder = Path(path)
            utilities.filesystem.mkdirp(args.output_folder)
            datastore = Datastore(args.output_folder)
            datastore.add_official_characters()
            
            output_folder = datastore.workspace
            script : Script = datastore.load_script(script_json, nights_json = nights_json)
            
            if args.i18n_fallback:
                script.options.i18n_fallback = True

            if args.bucket:
                script.options.bucket = True

            results = set()

            path = Renderer().render_script(script, output_folder = output_folder)
            results.add(path)

            if args.full:
                script.options.simple_nightorder = False
                path = Renderer().render_nightorder(script, output_folder = output_folder)
                results.add(path)
                
            if args.simple:
                script.options.simple_nightorder = True
                path = Renderer().render_nightorder(script, output_folder = output_folder)
                results.add(path)

            if args.postprocess:
                for path in results:
                    PDFTools.compress(path)
                    PDFTools.pngify(path)
            
            for path in results:
                print(str(path))
            
        except (ScriptmakerError, TypeError, Exception):
            print(traceback.format_exc())
    
    return 0


def cmd_tokenize (args):
    
    script_count = 0
    directory = Path(args.directory).resolve()
    
    if not args.output_folder:
        args.output_folder = Path(directory)
    utilities.filesystem.mkdirp(args.output_folder)
    datastore = Datastore(args.output_folder)
    
    if not args.exclude_official:
        datastore.add_official_characters()
    
    if args.extra_copies:
        with open(args.extra_copies) as f:
            copies_dict = json.load(f)
            character_copies = { utilities.sanitize.id(id): v for id, v in copies_dict.items() }
    else:
        character_copies = {}
    
    if not args.official_only:
        for json_path in directory.rglob('*.json'):
            with open(json_path) as json_file:
                script_json = json.load(json_file)
            if not isinstance(script_json, list) or len(script_json) == 0: 
                continue 
            
            try:
                entries = [ entry for entry in script_json if isinstance(entry, dict) ]
                ids = [ entry['id'] for entry in entries if 'id' in entry ]
                if '_meta' not in ids:
                    continue 
                script : Script = datastore.load_script(script_json)
                script_count += 1
            except (ScriptmakerError, TypeError):
                print(traceback.format_exc())
                continue
    
    else:
        script_json = [ {"id": "_meta", "name": "all"}, "atheist" ]
        script : Script = datastore.load_script(script_json)
        script_count = 1
    
    if script_count > 0:
        params = {
            'name': script.meta.name,
            'characters': script.characters,
            'character_copies': character_copies,
            "render_everything": True 
        }
        if args.character_size: params['character_token_size'] = args.character_size
        if args.reminder_size: params['reminder_token_size'] = args.reminder_size
        
        datastore.characters = dict(sorted(datastore.characters.items(), key=lambda item: item[0]))
        output_file = Tokenizer().render(datastore, ** params)
        
        if args.postprocess:
            PDFTools.compress(output_file)
            PDFTools.pngify(output_file)

    print(str(output_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())