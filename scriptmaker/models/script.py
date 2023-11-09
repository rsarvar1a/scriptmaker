
from scriptmaker import constants
from scriptmaker.data import Datastore
from scriptmaker.models import Character, Jinx
from scriptmaker.utilities import ScriptmakerValueError


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
        self.logo = logo


class ScriptOptions ():
    """
    Controls a variety of features related to script generation.
    """
    
    def __init__ (
        self, *,
        simple_nightorder = False, # if True, creates a script with rotatable nightorder
        i18n_fallback = False # if True, uses an internationally-friendly font for titles and character names
    ):
        """
        Creates a set of options for generating a script.
        """
        self.simple_nightorder = simple_nightorder
        self.i18n_fallback = i18n_fallback
        

class Script ():
    
    def __init__ (
        self, *,
        data : Datastore, # Your datastore containing all relevant characters
        meta = ScriptMeta(), # The _meta block from your custom script
        options = ScriptOptions() # Rendering options to attach to this script
    ):
        """
        Creates a new empty script.
        """
        self.meta = meta 
        self.options = options
        self.data = data
        
        self.by_team : dict[str, list[Character]] = {}
        self.characters : list[Character] = []
        self.jinxes : dict[str, list[Jinx]] = {}
        self.nightorder : dict[str, list[str]] = {}
                
    
    def add (self, id):
        """
        Adds a character to the script.
        """
        if id in self.characters:
            raise ScriptmakerValueError(f"script already contains character '{id}'")
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
            raise ScriptmakerValueError(f"character '{id}' is not on this script")
        self.characters.remove(self.data.get_character(id))
    
    
    def __calculate_jinxes (self):
        """
        Sets active jinxes on the script.
        """
        self.jinxes = {}
        all_ids = [ character.id for character in self.characters ]
        for character in self.characters:
            active_jinxes = [ Jinx(character.id, jinx['id'], jinx['reason']) for jinx in character.jinxes if jinx['id'] in all_ids ]
            self.jinxes[character.id] = active_jinxes
    
    
    def __calculate_nightorder (self):
        """
        Sets nightorder info on the script.
        """
        def __nightorder_for (night):
            """
            Calculates the night order for a given night.
            """
            acting_characters = [character for character in self.characters if character.nightinfo[night]['acts']]
            in_order = sorted(acting_characters, key=lambda character: character.nightinfo[night]['position'])
            return [ character.id for character in in_order ]
            
        for nightmeta in constants.NIGHT_META:
            if nightmeta not in self.characters:
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
