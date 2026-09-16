import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config.settings import settings

_basic = HTTPBasic()


def credentials_match(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(
        username.encode("utf-8"),
        settings.ADMIN_USERNAME.encode("utf-8"),
    )
    password_ok = secrets.compare_digest(
        password.encode("utf-8"),
        settings.ADMIN_PASSWORD.encode("utf-8"),
    )
    return user_ok and password_ok


def require_docs_auth(
    credentials: HTTPBasicCredentials = Depends(_basic),
) -> HTTPBasicCredentials:
    if not credentials_match(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials
