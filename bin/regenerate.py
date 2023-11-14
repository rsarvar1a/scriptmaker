
import json
import os
import re
import tempfile
import time
import urllib.request

from pathlib import Path

#
#   PARAMS
#

upstream = "data/upstream.json"
out_path = Path("scriptmaker/data/compiled/official.json").resolve()
img_path = Path("scriptmaker/data/icons").resolve()

#
#   UPSTREAM
#

upstream_url = "https://raw.githubusercontent.com/rsarvar1a/json-on-the-clocktower/main/data/generated/roles-combined.json"
urllib.request.urlretrieve(upstream_url, upstream)

#
#   CHARACTERS
#

# Load all non-nightmeta official characters (and old broken things) from our upstream.
with open(upstream, "r") as upstream_file:
    jotc : dict = json.load(upstream_file)
    output = jotc['character_by_id']   
    for key in ['DUSK', 'MINION', 'DEMON', 'DAWN', 'mephit']:
        output.pop(key, None)

# Load patches for each official character as well.
with open("data/patches.json", "r") as patches_file:
    patches : dict = json.load(patches_file)
    for id, patch in patches.items():
        for k, v in patch.items():
            output[id][k] = v

# Fix all the official token reminders because this source condenses actually-needed copies of tokens...
with open("data/physicalreminders.json") as patches_file:
    patches : dict = json.load(patches_file)
    for patch in patches:
        id = patch['id']
        for k in ['reminders', 'remindersGlobal']:
            output[id][k] = patch[k]

# Deal with inconsistent referencing in the old bra1n data.
names_to_ids = { output[id]['name']: id for id in output }
def to_id (id):
    if id in output.keys(): return id
    else: return names_to_ids[id]

# Regularize jinxes so that each source character owns their jinxes.
for src in jotc['jinxes']:
    src['id'] = to_id(src['id'])
    for jinx in src['jinx']:
        jinx['id'] = to_id(jinx['id'])
    output[src['id']]['jinxes'] = src['jinx']
    
# Save a sorted dictionary.
def sort_character (obj):
    k, v = obj 
    TEAMS = ['townsfolk', 'outsider', 'minion', 'demon', 'fabled', 'traveler']
    team_index = TEAMS.index(v['team'])
    return (team_index, k)

output = sorted(output.items(), key = sort_character)
output = { entry[0]: entry[1] for entry in output }

# Write to scriptmaker's compiled package resource.
with open(out_path, "w") as out_file:
    json.dump(output, out_file, indent=2)

#
#   IMAGES
#

DOMAIN = "https://wiki.bloodontheclocktower.com"
exceptions_path = "data/exceptions.json"

# Load the list of id exceptions.
with open(exceptions_path, "r") as exceptions_file:
    exceptions = json.load(exceptions_file)
    unsanitized_ids = [ exceptions[id] if id in exceptions else f"Icon_{id}" for id in output ]

# Re-sanitize the unsanitized IDs.
def sanitize(id):
    return re.sub('[^A-Za-z0-9]', '', id.replace('Icon_', '')).lower()

with tempfile.NamedTemporaryFile("w+b") as tmp:
    for unsanitized_id in unsanitized_ids:
        
        # We might have it; don't bother redoing if so. Delete files to force recrawl.
        id = sanitize(unsanitized_id)
        icon_path = Path(img_path, f"Icon_{id}.png")
        if os.path.exists(icon_path): continue
        
        # Read the wiki HTML and look for promising paths
        wiki_icon_link = f"{DOMAIN}/File:{unsanitized_id}.png"
        print(id, wiki_icon_link, end = " ")

        urllib.request.urlretrieve(wiki_icon_link, tmp.name)
        html = tmp.read().decode()
                
        # Get directly to the corresponding image, and save it.
        image_urls = re.search(r'images\/.\/..\/(?:Icon_)?[A-Za-z_]+.png', html)
        urllib.request.urlretrieve(f"{DOMAIN}/{image_urls[0]}", icon_path)
        
        # Log and seek back.
        print(len(html), image_urls)
        tmp.seek(0)

#
#   DONE
#
