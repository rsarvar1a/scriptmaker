
class ScriptmakerError(Exception):
    """
    A base class for exceptions in scriptmaker.
    """

class ScriptmakerValueError(ScriptmakerError):
    """
    An exception class for value and data errors in object creation or object linkage.
    """