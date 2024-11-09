class AListError(Exception):
    pass


class AuthenticationError(AListError):
    pass


class ServerError(AListError):
    pass


class SecurityWarning(Warning):
    pass


class DeprecationError(Exception):
    pass
