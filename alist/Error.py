class AListError(Exception):
    pass


class AuthenticationError(AListError):
    pass


class ServerError(AListError):
    pass
