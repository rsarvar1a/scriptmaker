
class KWArgPreparer ():
    """
    A wrapper for calling functions that accept keyword arguments with a single dictionary as an argument.
    """
        
    @classmethod
    def call (cls, func, kwargs)
        """
        Calls a function safely with an arbitrary dictionary of arguments by inspecting that function's signature.
        """
        arguments = cls.prepare(func, kwargs)        
        return func(** arguments)
    
    @classmethod 
    def prepare (cls, func, kwargs):
        """
        Given a function and a dictionary of arguments, provides a dictionary only containing keys in that function's signature.
        """
        signature = cls.__kwargs(func)
        return { k: v for k, v in kwargs.items() if k in signature }
    
    @classmethod
    def __kwargs (cls, func):
        """
        Inspect a function's signature to find its kwargs.
        """
        parameters = inspect.signature(func).parameters.values()
        return [parameter.name for parameter in parameters]
