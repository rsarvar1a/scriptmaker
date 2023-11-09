
import json
import pkgutil
import tempfile
import urllib

from pathlib import Path

from scriptmaker import constants
from scriptmaker.data import Icon, compiled, icons
from scriptmaker.models import Character, Script
from scriptmaker.utilities import ScriptmakerError, filesystem, sanitize


class ScriptmakerDataError(ScriptmakerError):
    """
    Raised when scriptmaker encounters a loading error.
    """


class Datastore ():
    """ 
    A collection of loaded characters living in a workspace.
    """
    
    def __init__ (self, workspace = None):
        """
        Scripts that are complete homebrews probably don't need to always load official resources, so they are initialized only with nightmeta.
        """
        self.workspace = workspace if workspace else tempfile.TemporaryDirectory()
        filesystem.mkdirp(self.workspace)
        
        self.characters : dict[str, Character] = {}
        self.icons : dict[str, Icon] = {}
        self.__load_nightmeta_characters()
    
    
    def add_character (self, character):
        """
        Adds a homebrew character to the data. 
        """
        if character.id in self.characters:
            raise ScriptmakerDataError(f"data already contains id '{character.id}'")
        self.characters[character.id] = character
        self.icons[character.id] = self.__fetch_icon(character.id)
        
    
    def add_official_characters (self):
        """
        Loads all official characters (and nightmeta) from the package.
        """
        try:
            official = json.loads(pkgutil.get_data(compiled.__name__, "official_characters.json"))
            for character in official:
                loaded_char = Character.from_dict(character)
                self.characters[loaded_char.id] = loaded_char
                self.icons[loaded_char.id] = self.__load_package_icon(loaded_char.id)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load official characters") from prev
    
    
    def export (self):
        """
        Saves the contents of this data to its workspace.
        """
        with open(Path(self.workspace, "characters.json"), "w") as json_file:
            json.dump(self.characters, json_file, indent=2)

        icons_path = Path(self.workspace, "icons")
        filesystem.mkdirp(icons_path)        
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

    
    def load_script (self, script_json):
        """
        Loads a script's homebrewed characters into this datastore, then builds the corresponding Script.
        """
        script = Script(self)
        
        for character in script_json:
            if character['id'] == "_meta":
                if 'name' in character: script.meta.name = character['name']
                if 'logo' in character: script.meta.logo = character['logo']
                if 'author' in character: script.meta.author = character['author']
            else:
                char = Character.from_dict(character)
                self.add_character(char)
                script.add(char.id)
                
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
            with tempfile.NamedTemporaryFile("w+") as tmp:
                urllib.request.urlretrieve(image_url, tmp.name)
                self.icons[id] = Icon(id, bytes(tmp.read()))
        except Exception as prev:
            raise ScriptmakerDataError(f"failed to fetch remote icon for character '{id}' from '{image_url}'")    
    
    
    def __load_nightmeta_characters (self):
        """
        Loads all nightmeta characters.
        """
        try:
            nightmeta = json.loads(pkgutil.get_data(compiled.__name__, "nightmeta.json"))
            for character in nightmeta:
                nightmeta_char = Character.from_dict(character)
                self.characters[nightmeta_char.id] = nightmeta_char
                self.icons[nightmeta_char.id] = self.__load_package_icon(nightmeta_char.id)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load nightmeta") from prev
    
    
    def __load_package_icon (self, id):
        """ 
        Loads an icon from the package. Only official and nightmeta characters can be loaded in this way.
        """
        try:
            icon_data = pkgutil.get_data(icons.__name__, "Icon_{id}.png")
            self.icons[id] = Icon(id, icon_data)
        except Exception as prev:
            raise ScriptmakerDataError("failed to load icon from package") from prev