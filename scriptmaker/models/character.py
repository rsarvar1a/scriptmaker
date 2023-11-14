from __future__ import annotations

import json
import re

import scriptmaker.constants as constants
import scriptmaker.utilities as utilities

class CharacterError(utilities.ScriptmakerValueError):
    """
    Raises an exception when scriptmaker detects invalid properties during character creation.
    """


class Character ():
    """
    Represents a Blood on the Clocktower character.
    """
    
    def __init__ (
        self, *, 
        id, name, team, ability, image, # Mandatory properties
        firstNight = None, firstNightReminder = "", otherNight = None, otherNightReminder = "", # Populates the nightorder
        reminders = [], remindersGlobal = [], setup = False, # Useful properties for token building
        jinxes = [] # A list of jinxes that originate from this character
    ):
        """
        Creates a new character from a list of properties. 
        It is *highly* recommended that you create characters using one of the class methods.
        """
        self.__warnings = [] # Anything not worthy of an actual exception is stored as a message.
        
        try:
            self.__set_mandatory_properties(id, name, team, ability, image)
            self.__check_setup(setup)
            self.__set_nightinfo(firstNight, firstNightReminder, otherNight, otherNightReminder)
            self.__set_reminders(reminders, remindersGlobal)
            self.__set_jinxes(jinxes)
        except utilities.ScriptmakerValueError as prev:
            raise CharacterError("failed to create character") from prev
    
    
    def get_warnings (self):
        """
        Returns the warnings produced for this character at creation.
        """
        return self.__warnings

        
    @classmethod
    def from_dict (cls, character_dict):
        """
        Creates a new character from a character dictionary.
        """
        prepared_arguments = utilities.KWArgPreparer.prepare(Character.__init__, character_dict)
        return cls(** prepared_arguments)
    
    
    @classmethod
    def from_json (cls, character_json):
        """
        Creates a new character from a JSON-encoded string.
        """
        try:
            character_info = json.loads(character_json)
            return cls.from_dict(character_info)
        except json.JSONDecodeError as prev:
            raise CharacterError("failed to create character") from prev
    
    
    def __check_setup (self, setup):
        """ 
        Sets whether or not this character affects setup, and checks that the ability agrees.
        """
        self.setup = setup
        
        ability_hint = re.search("\[.*\]", self.ability)
        if not self.setup and ability_hint:
            self.__warnings.append("no setup ability, but ability hints to one")
        elif self.setup and not ability_hint:
            self.__warnings.append("setup ability, but ability contains no setup condition")
        
    
    def __set_mandatory_properties(self, id, name, team, ability, image):
        """
        Validates and sets mandatory character properties.
        """
        
        # Validate the generic parameters.
        for prop in ['id', 'name', 'ability']:
            prop_value = eval(prop)
            if team != "_meta" and (not isinstance(prop_value, str) or prop_value == ""):
                raise utilities.ScriptmakerValueError(f"expected a non-empty string for property '{prop}', but received {prop_value}")
        
        # Sanitize the character ID.
        sanitized_id = utilities.sanitize.id(id)
        if sanitized_id != id:
            self.__warnings.append(f"sanitized id '{id}' to '{sanitized_id}'")
        
        # Validate the team name.
        sanitized_team = utilities.sanitize.team(team)
        if sanitized_team not in constants.TEAMS + ['_meta']:
            raise utilities.ScriptmakerValueError(f"expected one of [{', '.join(constants.TEAMS)}], but received {sanitized_team}")
        if sanitized_team != team:
            self.__warnings.append(f"sanitized team '{team}' to '{sanitized_team}'")

        # Ensure we have at least one valid image URL; scripts for the official app might contain a list of images to use for various alignments.
        image_err = None
        if isinstance(image, list):
            if len(image) == 0: image_err = f"expected a non-empty list for property 'image', received []"
            else: image_url = image[0]
        elif isinstance(image, str):
            if image == "": image_err = f"expected a non-empty string for property 'image', received ''"
            else: image_url = image
        if image_err: 
            raise utilities.ScriptmakerValueError(image_err)
        
        # Save our mandatory properties.
        self.id = sanitized_id
        self.name = name
        self.team = sanitized_team
        self.ability = ability
        self.image = image_url
        
        
    def __set_nightinfo (self, firstNight, firstNightReminder, otherNight, otherNightReminder):
        """
        Sets nightinfo for a character, and warns if properties are mismatched (e.g. a first night reminder is present with no first night index).
        """
        def __create_nightinfo_for (night, index, reminder):
            """
            Returns a nightinfo block for the given night.
            """
            acts = (index is not None and index > 0)
            night_repr = "the first night" if night == "first" else "other nights"
            
            if acts and not reminder:
                self.__warnings.append(f"{self.id} acts on {night_repr}, but has no reminder text")
            elif not acts and reminder:
                self.__warnings.append(f"{self.id} does not act on {night_repr}, but has reminder text")
            
            return { 
                'acts': acts, 
                'position': index, 
                'reminder': reminder 
            }
        
        self.nightinfo = {
            "first": __create_nightinfo_for("first", firstNight, firstNightReminder),
            "other": __create_nightinfo_for("other", otherNight, otherNightReminder)
        }
        
    
    def __set_reminders (self, reminders, remindersGlobal):
        """ 
        Sets reminders, ignoring anything that is not a string.
        """
        for reminder in reminders + remindersGlobal:
            if not isinstance(reminder, str):
                self.__warnings.append(f"reminder {reminder} is not a string; ignoring")
        self.reminders = reminders
        self.remindersGlobal = remindersGlobal
    
    
    def __set_jinxes (self, jinxes):
        """
        Sanitizes and sets jinxes that originate at this character.
        """
        if not isinstance(jinxes, list):
            self.__warnings.append(f"expected list for property 'jinxes', but received {jinxes}; ignoring")
        else:
            self.jinxes = []
            for jinx in jinxes:
                for prop in ['id', 'reason']:
                    if prop not in jinx:
                        self.__warnings.append(f"invalid jinx {jinx} (missing prop '{prop}'); ignoring")
                        break
                else:
                    sanitized_target = utilities.sanitize.id(jinx['id'])
                    if sanitized_target != jinx['id']:
                        self.__warnings.append(f"sanitized jinxed character '{jinx['id']}' to '{sanitized_target}")
                    self.jinxes.append({ 'id': sanitized_target, 'reason': jinx['reason'] })
                    continue
