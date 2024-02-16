class AListError(Exception):
    pass
class AuthenticationError(ValueError):
    pass

class ServerError(AListError):
    pass