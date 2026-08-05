class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class UserAlreadyExistsError(Exception):
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        super().__init__(f"User with username '{username}' or email '{email}' already exists")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Invalid username or password")


class InvalidRefreshTokenError(Exception):
    def __init__(self):
        super().__init__("Invalid, expired, or already used refresh token")
