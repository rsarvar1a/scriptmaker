
import pkgutil


COMMON = [
    "leaf-first.png",
    "leaf-other.png",
    "leaf-reminder-1.png",
    "leaf-reminder-2.png",
    "leaf-reminder-3.png",
    "leaf-reminder-4.png",
    "leaf-reminder-5.png",
    "leaf-reminder-6.png",
    "leaf-reminder-7.png",
    "leaf-setup.png",
    "token.png",
    "token2.png"
]

def get_data (file):
    """ 
    Gets a template file's content.
    """
    return pkgutil.get_data(__package__, file)
