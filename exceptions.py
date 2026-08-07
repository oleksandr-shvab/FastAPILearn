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


class InvalidGoogleTokenError(Exception):
    def __init__(self):
        super().__init__("Invalid or unverifiable Google token")


class MembershipAlreadyExistsError(Exception):
    def __init__(self, project_id: int, user_id: int):
        self.project_id = project_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is already a member of project {project_id}")


class MembershipNotFoundError(Exception):
    def __init__(self, project_id: int, user_id: int):
        self.project_id = project_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is not a member of project {project_id}")


class LastOwnerError(Exception):
    def __init__(self, project_id: int):
        self.project_id = project_id
        super().__init__(f"Project {project_id} must have at least one owner")
