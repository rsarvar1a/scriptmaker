
import base64
import io 

from pathlib import Path
from PIL import Image


class Icon ():
    """ 
    A wrapper around a PIL Image corresponding to a character's icon.
    Scriptmaker only supports a single icon per character, and does not deal in alternate alignments.
    """
    
    def __init__ (self, id, bytes):
        """ 
        Creates an icon from the bytes of a PNG image.
        """
        self.id = id
        self.icon = Image.open(io.BytesIO(bytes))
    
    
    def base64 (self):
        """ 
        Provides a b64 encoding of the image data.
        """
        buffer = io.BytesIO()
        self.icon.save(buffer)
        return base64.b64encode(buffer.getvalue())
    
    
    def save (self, dirname):
        """ 
        Saves the image to a path.
        """
        self.icon.save(Path(dirname, f"{self.id}.png"))
