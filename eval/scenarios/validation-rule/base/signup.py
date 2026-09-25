MIN_PASSWORD_LENGTH = 8


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("password must be at least 8 characters")
