import os
import sys
from datetime import datetime

import jwt
from fastapi import HTTPException, Request, status

from db import SessionLocal
from models import User

TOKEN_HEADER = 'X-Access-Token'  # noqa: S105
JSON_MIMETYPE = 'application/json'
SECRET_KEY = os.getenv('SECRET_KEY')


def check_mimetype(request: Request, mimetype: str = JSON_MIMETYPE) -> None:
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith(mimetype):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f'Content-Type header must be {mimetype}',
        )


def validate_token(token: str) -> None:
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Authentication header missing.',
        )
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f'Authentication failed: {e}.',
        )
    db = SessionLocal()
    user_id = decoded_token.get('user_id')
    user = db.query(User).filter_by(id=user_id).first()
    db.close()
    if datetime.fromisoformat(user.last_pwd_change) > datetime.fromisoformat(
        decoded_token.get('last_pwd_change'),
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Token expired.')


def get_user_id(token: str) -> str:
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return decoded_token.get('user_id')


if __name__ == '__main__':
    sys.exit(0)
