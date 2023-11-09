
import re


def id (id):
    """
    Converts character IDs into purely alphanumeric identifiers.
    """
    return re.sub('[^0-9A-Za-z]', '', id)


def team (team):
    """
    Handles some ambiguities in team names.
    """
    if team == 'traveller': return 'traveler'
    return team
