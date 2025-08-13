import os

import jwt
from fastapi import HTTPException, Request, status

TOKEN_HEADER = 'X-Access-Token'
JSON_MIMETYPE = 'application/json'
SECRET_KEY = os.getenv('SECRET_KEY')


def check_mimetype(request: Request, mimetype: str = JSON_MIMETYPE) -> None:
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith(mimetype):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f'Content-Type header must be {mimetype}'
        )


def validate_token(token: str) -> None:
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Authentication header missing.'
        )
    try:
        jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f'Authentication failed: {e}.'
        )


def get_user_id(token: str) -> str:
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return decoded_token.get('user_id')


if __name__ == '__main__':
    exit(0)
