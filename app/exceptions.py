from typing import Any


class AppError(Exception):
    status_code = 400
    headers: dict[str, str] | None = None
    code: str = "app_error"
    message_template: str = "An unexpected error occurred"

    def __init__(self, **params: Any) -> None:
        self.params = params
        super().__init__(self.code)

    @property
    def message(self) -> str:
        return self.message_template.format(**self.params)


class UserNotFoundError(AppError):
    status_code = 404
    code = "user_not_found"
    message_template = "User {user_id} not found"

    def __init__(self, user_id: int) -> None:
        super().__init__(user_id=user_id)


class UserAlreadyExistsError(AppError):
    status_code = 409
    code = "user_already_exists"
    message_template = "User with username '{username}' or email '{email}' already exists"

    def __init__(self, username: str, email: str) -> None:
        super().__init__(username=username, email=email)


class InvalidCredentialsError(AppError):
    status_code = 401
    headers = {"WWW-Authenticate": "Bearer"}
    code = "invalid_credentials"
    message_template = "Invalid username or password"


class InvalidRefreshTokenError(AppError):
    status_code = 401
    headers = {"WWW-Authenticate": "Bearer"}
    code = "invalid_refresh_token"
    message_template = "Invalid, expired, or already used refresh token"


class InvalidGoogleTokenError(AppError):
    status_code = 401
    code = "invalid_google_token"
    message_template = "Invalid or unverifiable Google token"
