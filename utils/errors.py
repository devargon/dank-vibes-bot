from discord.ext import commands

class ArgumentBaseError(commands.UserInputError):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ThisEmpty(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"No valid argument was converted. Which makes {arg} as empty.", **kwargs)

class DonationCategoryDoesNotExist(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"The donation category {arg} does not exist.", **kwargs)

class RoleNotFound(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"I couldn't find a role called {arg}.", **kwargs)

class UserNotFound(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"I couldn't find {arg}, is this even a valid user?", **kwargs)
    
class IntegratedRoleError(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"**{arg}** is an integrated role.", **kwargs)

class DefaultRoleError(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"That's the default role.", **kwargs)

class NotInBanBattle(ArgumentBaseError):
    def __init__(self):
        super().__init__(message="This command can only be invoked in `Dank Vibes Ban Mania` server.")

class InvalidDatabase(ArgumentBaseError):
    def __init__(self, arg, **kwargs):
        super().__init__(message=f"**{arg}** is not a valid database.", **kwargs)

class NicknameIsManaged(ArgumentBaseError):
    def __init__(self, **kwargs):
        super().__init__(message=f"The user you're interacting with has their nickname managed/frozen by the bot.", **kwargs)