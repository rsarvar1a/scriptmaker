
import os

from pathlib import Path 

from scriptmaker.utilities import ScriptmakerError


class ScriptmakerFSError(ScriptmakerError):
    """
    Raised when the filesystem utilities locate an error.
    """


def mkdirp (directory):
    """ 
    Roughly emulates mkdir -p.
    """
    
    if os.path.exists(directory) and not os.path.isdir(directory):
        raise ScriptmakerFSError(f'cannot create directory at {directory}: file exists')
    
    if not os.path.exists(directory):
        os.mkdir(directory)