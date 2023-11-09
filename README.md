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

## Creating a script

0. Import everything you need.
```python
from scriptmaker import Character, Data, Script, ScriptmakerError
```

1. Create a data store for your new script.
```python
# Create a datastore (leaving it blank uses a temporary directory)
my_datastore : Data = Data("my/output/directory")

# Load the official characters into it, if you want
my_datastore.add_official_characters()
```

2. Load a script.json file.
```python
with open("my/script.json", "r") as json_file:
    my_script_json = json.load(json_file)

# Loads the characters into the datastore, then builds a script object too
my_script : Script = my_datastore.load_script(my_script_json)
```

3. Set your desired options on the script if not already in the script.json.
```python
# Metas are set if there was a _meta block in the script.json
my_script.meta.author = "rsarvar1a"

# Options have defaults; see ScriptOptions()
my_script.options.i18n_fallback = True
```

4. Render it!
```python
my_script.render()
```

# Changelog

## 1.0.0 - packages are neat

- Character updates:
    - adds the Ojo
- Features:
    - adds a fallback switch for translations that didn't play well with default style
- **Breaking changes**:
    - if you were using the (unpackaged) version of `scriptmaker`, you will need to write your own scripts