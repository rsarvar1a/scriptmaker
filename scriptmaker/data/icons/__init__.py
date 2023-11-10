
import pkgutil


def get_data (file):
    """ 
    Gets a compiled file's content.
    """
    return pkgutil.get_data(__package__, file)
