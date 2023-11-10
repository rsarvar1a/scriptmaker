
import argparse 
import io
import json
import sys
import tempfile
import urllib.request
   
from scriptmaker import Datastore, Script, Renderer


def main ():
    # Figure out what our user wants to do. We accept either a URL to a script (that we fetch) or a JSON file.
    parser = argparse.ArgumentParser()
    
    inputs = parser.add_argument_group('script inputs')
    source = inputs.add_mutually_exclusive_group(required = True) 
    source.add_argument('--url')
    source.add_argument('--script')
    inputs.add_argument('--nights', default = None)
    
    output = parser.add_argument_group('output options')
    output.add_argument('--save-to', default = None)
    output.add_argument('--export', action = 'store_true')
    
    options = parser.add_argument_group('script options')
    options.add_argument('--simple-nightorder', action = 'store_true')
    options.add_argument('--i18n-fallback', action = 'store_true')
    
    args = parser.parse_args()
    
    # Create a datastore.
    datastore = Datastore(args.save_to)
    datastore.add_official_characters()
    
    # Load our script.
    if args.script:
        with open(args.script) as json_file:
            script_json = json.load(json_file)
    else:
        buffer = io.BytesIO()
        urllib.request.urlretrieve(args.url, buffer)
        script_json = json.load(buffer)
    
    # Load our nights if given.
    if args.nights:
        with open(args.nights) as json_file:
            nights_json = json.load(json_file)
    else:
        nights_json = None
    
    # Apply options.
    script = datastore.load_script(script_json, nights_json = nights_json)
    script.options.simple_nightorder = args.simple_nightorder
    script.options.i18n_fallback = args.i18n_fallback
    
    # Render out our PDFs (currently if the datastore was temporary then I'm not sure how these could possibly be valid).
    if args.export:
        datastore.export()
    output_files = Renderer().render(script)
    
    # Success!
    print(output_files)
    return 0


if __name__ == "__main__":
    sys.exit(main())