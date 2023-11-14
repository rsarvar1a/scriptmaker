
import pkgutil

from . import tokens 


COMMON = [
    "CormorantGaramond-Bold.ttf",
    "CormorantGaramond-Medium.ttf",
    "Dumbledor 1.ttf",
    "common.css"
]

def get_data (file):
    """ 
    Gets a template file's content.
    """
    return pkgutil.get_data(__package__, file)

