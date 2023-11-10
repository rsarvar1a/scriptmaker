from __future__ import annotations

import json
import pkgutil
import tempfile
import urllib

from pathlib import Path

from . import compiled, icons
from .icon import Icon

import scriptmaker.constants as constants
import scriptmaker.models as models
import scriptmaker.utilities as utilities


class ScriptmakerDataError(utilities.ScriptmakerError):
    """
    Raised when scriptmaker encounters a loading error.
    """

class DatastoreEncoder (json.JSONEncoder):
    """ 
    Flattens Characters into schema-compatible blocks, and jinxes into id-reason blocks.
    """
    def default (self, obj):
        if isinstance(obj, models.Character):
            return {
                "id": obj.id,
                "name": obj.name,
                "team": obj.team,
                "ability": obj.ability,
                "image": obj.image,
                
                "firstNight": obj.nightinfo['first']['position'],
                "firstNightReminder": obj.nightinfo['first']['reminder'],
                "otherNight": obj.nightinfo['other']['position'],
                "otherNightReminder": obj.nightinfo['other']['reminder'],
                
                "jinxes": obj.jinxes
            }
        elif isinstance(obj, (models.Jinx, models.ScriptMeta, models.ScriptOptions)):
            return obj.__dict__
        else:
            return self.encode(obj)
    

class Datastore ():
    """ 
    A collection of loaded characters living in a workspace.
    """
    
    def __init__ (self, workspace = None):
        """
        Scripts that are complete homebrews probably don't need to always load official resources, so they are initialized only with nightmeta.
        """
        self.workspace = workspace if workspace else tempfile.TemporaryDirectory()
        utilities.filesystem.mkdirp(self.workspace)
        
        self.characters : dict[str, models.Character] = {}
        self.icons : dict[str, models.Icon] = {}
        self.__load_nightmeta_characters()
    
    
    def add_character (self, character):
        """
        Adds a homebrew character to the data. 
        """
        if character.id in self.characters:
            raise ScriptmakerDataError(f"data already contains id '{character.id}'")
        self.characters[character.id] = character
        self.__fetch_icon(character.id)
        
    
    def add_official_characters (self):
        """
        Loads all official characters (and nightmeta) from the package.
        """
        try:
            official = json.loads(compiled.get_data("official.json"))
            for _, character in official.items():
                character['image'] = 'local-icon'
                loaded_char = models.Character.from_dict(character)
                self.characters[loaded_char.id] = loaded_char
                self.__load_package_icon(loaded_char.id)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load official characters") from prev
    
    
    def export (self):
        """
        Saves the contents of this data to its workspace.
        """
        with open(Path(self.workspace, "characters.json"), "w") as json_file:
            json.dump(self.characters, json_file, cls = DatastoreEncoder, indent=2)

        icons_path = Path(self.workspace, "icons")
        utilities.filesystem.mkdirp(icons_path)        
        for character in self.icons:
            self.icons[character].save(icons_path)
        
        
    def get_character (self, id):
        """
        Get a character in the dataset.
        """
        if id not in self.characters:
            raise ScriptmakerDataError(f"id '{id}' is not a character")
        return self.characters[id]

    
    def get_icon (self, id):
        """ 
        Get a character icon from the dataset.
        """
        if id not in self.icons:
            raise ScriptmakerDataError(f"id '{id}' has no icon")
        return self.icons[id]

    
    def load_script (self, script_json, nights_json = None):
        """
        Loads a script's homebrewed characters into this datastore, then builds the corresponding Script.
        """
        script = models.Script(data = self, nights = nights_json)
        
        for character in script_json:
            # Handle modern-format base3+experimental scripts.
            if isinstance(character, str):
                id = utilities.sanitize.id(character)
                if id not in self.characters:
                    raise ScriptmakerDataError(f"character '{character}' (-> '{id}') is not an official character; cannot be string-loaded")
                script.add(id)
                continue

            # Otherwise, figure out what's going on with this character.                
            if character['id'] == "_meta":
                if 'name' in character: script.meta.name = character['name']
                if 'author' in character: script.meta.author = character['author']
                if 'logo' in character: script.meta.add_logo(character['logo'])
            else:
                character['id'] = utilities.sanitize.id(character['id'])
                if character['id'] in self.characters:
                    char = self.get_character(character['id']).__dict__
                    id = char['id']
                else:
                    char = models.Character.from_dict(character)
                    self.add_character(char)
                    id = char.id
                script.add(id)
                
        return script
    
    
    def remove_character (self, id):
        """ 
        Removes a character from this dataset.
        """
        self.characters.pop(id, None)
        self.icons.pop(id, None)
        
    
    def __fetch_icon (self, id):
        """ 
        Fetches the remote icon for the given character.
        """
        try:
            image_url = self.get_character(id).image
            with tempfile.NamedTemporaryFile("w+b") as tmp:
                urllib.request.urlretrieve(image_url, tmp.name)
                self.icons[id] = Icon(id, tmp.read())
        except Exception as prev:
            raise ScriptmakerDataError(f"failed to fetch remote icon for character '{id}' from '{image_url}'")    
    
    
    def __load_nightmeta_characters (self):
        """
        Loads all nightmeta characters.
        """
        try:
            nightmeta = json.loads(compiled.get_data("nightmeta.json"))
            for character in nightmeta:
                nightmeta_char = models.Character.from_dict(character)
                self.characters[nightmeta_char.id] = nightmeta_char
                self.__load_package_icon(nightmeta_char.id)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load nightmeta") from prev
    
    
    def __load_package_icon (self, id):
        """ 
        Loads an icon from the package. Only official and nightmeta characters can be loaded in this way.
        """
        try:
            icon_data = icons.get_data(f"Icon_{id}.png")
            self.icons[id] = Icon(id, icon_data)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load icon from package") from prev