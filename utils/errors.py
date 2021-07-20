from discord.ext import commands

class ArgumentBaseError(commands.UserInputError):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ThisEmpty(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"No valid argument was converted. Which makes {arg} as empty.", **kwargs)

class RoleNotFound(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"I couldn't find a role called {arg}.", **kwargs)

class UserNotFound(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"I couldn't find {arg}, is this even a valid user?", **kwargs)