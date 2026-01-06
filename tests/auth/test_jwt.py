from datetime import datetime, timezone

from app.constants.role import Role
from app.core.config import TOKEN_ISSUER
from app.core.security import create_access_token, verify_access_token
from app.schemas.user import UserData


def test_create_and_verify_access_token_success():
    user = UserData(id=1, email="user@example.com", role=Role.USER, is_active=True)
    access_token = create_access_token(user)

    payload = verify_access_token(access_token)

    assert access_token.startswith("eyJ")  # jwt 토큰은 eyJ로 시작함
    assert payload.sub == user.id
    assert payload.user.email == user.email
    assert payload.exp > datetime.now(tz=timezone.utc)
    assert payload.iss == TOKEN_ISSUER
    timediff = datetime.now(tz=timezone.utc) - payload.iat
    assert timediff.seconds < 3
