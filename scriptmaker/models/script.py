from __future__ import annotations

import io
import tempfile
import urllib.request

import scriptmaker.constants as constants
import scriptmaker.data as data
import scriptmaker.models as models
import scriptmaker.renderer as renderer
import scriptmaker.utilities as utilities

class ScriptMeta ():
    """ 
    Represents meta properties of a script, such as its name, author, logo, etc.
    """
    
    def __init__ (
        self, *,
        name = "Custom Script",
        author = None,
        logo = None
    ):
        self.name = name 
        self.author = author   
        self.add_logo(logo)
        
        
    def add_logo (self, logo):
        """ 
        Tries to set a logo.
        """
        self.logo = logo
        self.icon = None
        
        if self.logo:
            try: 
                with tempfile.NamedTemporaryFile() as tmpfile:
                    urllib.request.urlretrieve(self.logo, tmpfile.name)
                    self.icon = data.Icon('script_logo', tmpfile.read())
            except utilities.ScriptmakerError as prev:
                raise utilities.ScriptmakerDataError(f"failed to load script logo from '{self.logo}'")
        else:
            self.icon = None


class ScriptOptions ():
    """
    Controls a variety of features related to script generation.
    """
    
    def __init__ (
        self, *,
        bucket = False,
        simple_nightorder = False, # if True, creates a script with rotatable nightorder
        i18n_fallback = False, # if True, uses an internationally-friendly font for titles and character name
        force_jinxes = False
    ):
        """
        Creates a set of options for generating a script.
        """
        self.bucket = bucket
        self.simple_nightorder = simple_nightorder
        self.i18n_fallback = i18n_fallback
        self.force_jinxes = force_jinxes
        

class Script ():
    
    def __init__ (
        self, *,
        data : data.Datastore, # Your datastore containing all relevant characters
        nights = None, # An optional nightorder JSON
        meta = None, # The _meta block from your custom script
        options = None # Rendering options to attach to this script
    ):
        """
        Creates a new empty script.
        """
        if not meta: meta = ScriptMeta()
        if not options: options = ScriptOptions()
        
        self.meta = meta 
        self.options = options
        self.data = data
        
        self.by_team : dict[str, list[models.Character]] = {}
        self.characters : list[models.Character] = []
        self.jinxes : dict[str, list[models.Jinx]] = {}
        self.nightorder : dict[str, list[str]] = {}
        self.nights = nights
                
    
    def add (self, id):
        """
        Adds a character to the script.
        """
        if id in self.characters:
            raise utilities.ScriptmakerValueError(f"script already contains character '{id}'")
        self.characters.append(self.data.get_character(id))
    
    
    def finalize (self):
        """
        Calculates jinxes and nightorder for the script. Must be called prior to being used by any renderer.
        """
        self.__partition_by_teams()
        self.__calculate_jinxes()
        self.__calculate_nightorder()

    
    def remove (self, id):
        """
        Removes a character from the script.
        """
        if id not in self.characters:
            raise utilities.ScriptmakerValueError(f"character '{id}' is not on this script")
        self.characters.remove(self.data.get_character(id))
    
    
    def render (self, **options):
        """
        Shortcut to rendering; see scriptmaker.Renderer.render().
        """
        renderer.Renderer().render(self, **options)
    
    
    def __calculate_jinxes (self):
        """
        Sets active jinxes on the script.
        """
        self.jinxes = {}
        all_ids = [ character.id for character in self.characters ]
        for character in self.characters:
            active_jinxes = [ models.Jinx(character.id, jinx['id'], jinx['reason']) for jinx in character.jinxes if jinx['id'] in all_ids ]
            self.jinxes[character.id] = active_jinxes
    
    
    def __calculate_nightorder (self):
        """
        Sets nightorder info on the script.
        """
        def __nightorder_for (night):
            """
            Calculates the night order for a given night.
            """
            if not self.nights:
                acting_characters = [character for character in self.characters if character.nightinfo[night]['acts']]
                in_order = sorted(acting_characters, key=lambda character: character.nightinfo[night]['position'])
                return [ character.id for character in in_order ]
            else:
                # Just trust it, honestly...
                return self.nights[night]
            
        for nightmeta in constants.NIGHT_META:
            if nightmeta not in [ character.id for character in self.characters ]:
                self.characters.append(self.data.get_character(nightmeta))

        self.nightorder = {
            "first": __nightorder_for('first'),
            "other": __nightorder_for('other')
        }
    
    
    def __partition_by_teams (self):
        """
        Splits the script characters into their teams.
        """
        self.by_team = {}
        for team in constants.TEAMS:
            team_members = [character for character in self.characters if character.team == team]
            self.by_team[team] = team_members
