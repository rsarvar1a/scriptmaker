
import pkgutil

from . import tokens 


COMMON = [
    "19mm-blank.png",
    "38mm-blank.png",
    "paper.jpg",
    "parchment.jpg",
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

