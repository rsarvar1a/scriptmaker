# Scriptmaker

A PDF writer for Blood on the Clocktower scripts. 

Scriptmaker includes some special features:
- support for modern and legacy base3+experimental custom scripts
- **homebrew character support** via the official app's character schema
  - as a result, supports translations too!
- nightorder styles: single-sided rotated, or double-sided full-text
- i18n support with fallback rendering modes

Significant credit goes to [chizmw](https://github.com/chizmw/botc-custom-script-json2pdf) for inspiration and assets!

## Stack
- Python
- `poetry`
- `jinja2`

# Examples

## Trouble Brewing

Here's scriptmaker's default output for the official Trouble Brewing script.

<p float="left">
  <a href="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-script-1.png">
    <img src="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-script-1.png" width="32%">
  </a>
  <a href="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-nights-1.png">
    <img src="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-nights-1.png" width="32%">
  </a>
  <a href="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-nights-2.png">
    <img src="examples/Trouble Brewing/Standard/pdf/pages/Trouble_Brewing-nights-2.png" width="32%">
  </a>
</p>

You can also choose to generate simple nightorders.

<p float="left">
  <a href="examples/Trouble Brewing/Simple/pdf/pages/Trouble_Brewing-script-1.png">
    <img src="examples/Trouble Brewing/Simple/pdf/pages/Trouble_Brewing-script-1.png" width="48%">
  </a>
  <a href="examples/Trouble Brewing/Simple/pdf/pages/Trouble_Brewing-nights-1.png">
    <img src="examples/Trouble Brewing/Simple/pdf/pages/Trouble_Brewing-nights-1.png" width="48%">
  </a>
</p>

## Custom script & homebrew

Homebrewed content and custom logos are also supported.

<p float="left">
  <a href="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-script-1.png">
    <img src="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-script-1.png" width="32%">
  </a>
  <a href="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-nights-1.png">
    <img src="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-nights-1.png" width="32%">
  </a>
  <a href="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-nights-2.png">
    <img src="examples/Fall Of Rome/pdf/pages/Fall_of_Rome-nights-2.png" width="32%">
  </a>
</p>

# Usage

## Installation

Scriptmaker requires the following non-Python dependencies:
```
ghostscript
poppler-utils
pango
```

Install the package with your package manager of choice.

```sh
pip install scriptmaker
poetry add scriptmaker
...
```

## Using the CLI

```yaml
scriptmaker (make-pdf | tokenize)
```

```yaml
scriptmaker make-pdf <inputs> [output] [options]

  inputs:
    (--script path/to/script.json | --url https://script.json | --recurse path/to/folder/) # Sources a script.
    [--nights path/to/nights.json] # Supplies a custom night order.
  
  output:
    [--output-folder path/to/folder/] # Creates build/ and pdf/ folders under this directory.
  
  options:
    [--full] # Creates a full-text two-sided nightorder
    [--simple] # Creates a simple, rotatable nightorder for physical printing
    [--i18n-fallback] # Tries to resolve issues with non-Latin character rendering
    [--postprocess] # Compresses PDFs and generates PNGs for pages
```

```yaml
scriptmaker tokenize <inputs> [output] [options]

  inputs:
    directory # Recurses over it, adds all scripts to a datastore, and prints the result.
  
  output:
    [--output-folder path/to/folder/] # Creates build/ and pdf/ folders under this directory.
  
  options:
    [--character-size size-in-mm] # Determines the size in millimetres of character tokens; default 45.
    [--reminder-size size-in-mm] # Determines the size in millimetres of reminder tokens; default 19.
    [--extra-copies path/to/copies.json] # A key-value dict of character IDs and token counts, if you wish to generate extra copies.
    [--official-only | --exclude-official] # Either only print base3 + experimental tokens, or don't add them at all (good for homebrews).
    [--postprocess] # Compresses PDFs and generates PNGs for pages
```

## Using the package

0. Import everything you need.
```python
from scriptmaker import Character, Datastore, Script, PDFTools, Renderer, ScriptmakerError
```

1. Create a data store for your new script.
```python
# Create a datastore (leaving it blank uses a temporary directory)
my_datastore : Datastore = Datastore("my/output/directory/")

# Load the official characters into it, if you want
my_datastore.add_official_characters()
```

2. Load a script.json file.
```python
with open("my/script.json", "r") as json_file:
    my_script_json = json.load(json_file)

# Perhaps you have a custom nightorder.
with open("my/nightorder.json", "r") as nightorder_file:
    my_nightorder = json.load(nightorder_file)

# Loads the characters into the datastore, then builds a script object too
my_script : Script = my_datastore.load_script(my_script_json, nightorder_json = my_nightorder)
```

3. Set your desired options on the script if not already in the script.json.
```python
# Metas are automatically set if there was a _meta block in the script.json
my_script.meta.author = "rsarvar1a"
my_script.meta.add_logo("https://my/logo/url.png")

# Options have defaults; see ScriptOptions()
my_script.options.i18n_fallback = True
```

4. Render it!
```python
outputs = set()

# Renders to the datastore path, if no output_folder is given
outputs.add(Renderer().render_script(my_script), output_folder = None)
outputs.add(Renderer().render_nightorder(my_script))
```

5. Postprocess your PDFs.
```python
for path in outputs:
  PDFTools.compress(path)
  PDFTools.pngify(path)
```
