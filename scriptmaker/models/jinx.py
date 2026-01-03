
import re


class Jinx ():
    """
    A regularization of a character jinx, moved out of the character class and converted to a pair of ids and a reason.
    """
    
    def __init__ (self, src, dst, reason):
        """
        Creates a new jinx; additionally attempts to determine whether or not it is a hate jinx.
        """
        self.src_id = src
        self.dst_id = dst
        self.reason = reason 
        self.is_hate = (re.search('Only one', reason) is not None)
