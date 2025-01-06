import json
import os
import sqlite3

import jwt
from fastapi import HTTPException, Request, status

DB_PATH = './db.db'
TOKEN_HEADER = 'X-Access-Token'


def create_database() -> None:
    if os.path.exists(DB_PATH) and os.path.isfile(DB_PATH):
        print('DB file already exists.')
        return

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # todo table
        cur.execute("""
            CREATE TABLE todo (
            todo_id INT PRIMARY KEY NOT NULL,
            todo TEXT,
            created_at TEXT,
            done int,
            owner TEXT,
            FOREIGN KEY (owner) REFERENCES user(user_id)
            );
        """)
        # user table
        cur.execute("""
            CREATE TABLE user (
            user_id TEXT PRIMARY KEY NOT NULL,
            user_name TEXT NOT NULL,
            pwd_hash TEXT NOT NULL
            );
        """)
        print('New DB created with "todo" and "user" table.')

        conn.commit()


def get_last_id() -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT MAX(todo_id) FROM todo;')
        max_id = cur.fetchone()[0]

    return max_id if max_id is not None else 0


def check_mimetype(request: Request, mimetype: str) -> None:
    if request.headers.get('Content-Type') != mimetype:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Set the correct headers in your request.'
        )


async def get_json_data(request: Request) -> dict[str, [str | bool]] | None:
    try:
        data = await request.json()
        return data
    except json.JSONDecodeError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Provide proper json in your request body.'
        )


def validate_token(token: str) -> None:
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Authentication header missing.'
        )
    secret = os.getenv('SECRET_KEY')
    try:
        jwt.decode(token, secret, 'HS256')
    except jwt.PyJWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f'Authentication failed with error {e}.'
        )


def get_user_id(token: str) -> str:
    secret = os.getenv('SECRET_KEY')
    decoded_token = jwt.decode(token, secret, 'HS256')
    return decoded_token.get('user_id')


if __name__ == '__main__':
    exit(0)
