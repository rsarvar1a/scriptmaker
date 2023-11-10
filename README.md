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

## Custom script & homebrew

# Usage

## Installation

Install the package with your package manager of choice.

```sh
pip install scriptmaker
```
```sh
poetry add scriptmaker
```
```sh
...
```

## Using the CLI

```
scriptmaker <inputs> [outputs] [options]

    inputs: (--url | --script)
        --url https://url/to/script.json
        --script path/to/script.json
        --nights path/to/nights.json
    
    outputs:
        --export
        --save-to path/to/folder/

    options:
        --i18n-fallback
        --simple-nightorder
```

## Using the package

0. Import everything you need.
```python
from scriptmaker import Character, Datastore, Script, Render, ScriptmakerError
```

1. Create a data store for your new script.
```python
# Create a datastore (leaving it blank uses a temporary directory)
my_datastore : Datastore = Datastore("my/output/directory")

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
outputs = Renderer().render(my_script)
        # my_script.render()
```

# Changelog

## 1.0.0 - packages are neat

- Character updates:
    - adds all experimental characters up to the Ojo
- Features:
    - shows a script's author and logo if those properties are in the `_meta`
- **Breaking changes**:
    - if you were using the (unpackaged) version of `scriptmaker`, you will need to write your own scripts