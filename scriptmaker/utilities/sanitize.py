
import re


def id (id):
    """
    Converts character IDs into purely alphanumeric identifiers.
    """
    return re.sub('[^0-9A-Za-z]', '', id)


def name (name):
    """
    Creates a safe string for paths.
    """
    replace = re.sub('[\(\)!?]', '', name)
    replace = replace.replace(' ', '_').replace('&', 'and')
    return replace


def team (team):
    """
    Handles some ambiguities in team names.
    """
    if team == 'traveller': return 'traveler'
    return team
