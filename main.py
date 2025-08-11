import datetime
import os
import sqlite3
from uuid import uuid4

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import APIKeyHeader

import helpers

DB_PATH = helpers.DB_PATH
SECRET_KEY = os.getenv('SECRET_KEY')
JSON_MIMETYPE = 'application/json'

load_dotenv()
app = FastAPI()
helpers.create_database()
header_scheme = APIKeyHeader(name=helpers.TOKEN_HEADER)


@app.get('/')
def index():
    return {
        'message': 'All good.'
    }


@app.post('/signup')
async def signup(request: Request):
    helpers.check_mimetype(request, JSON_MIMETYPE)

    data = await helpers.get_json_data(request)
    user_name = data.get('user')
    pwd = data.get('password')

    if user_name is None or pwd is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Fields "user" or "password" missing from request body.'
        )

    if len(pwd) < 8:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Password must be at least 8 characters long.'
        )

    user_id = str(uuid4())
    salt = bcrypt.gensalt()
    pwd_hash = bcrypt.hashpw(pwd.encode('UTF-8'), salt)
    pwd_hash = pwd_hash.decode('UTF-8')

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO user (user_id, user_name, pwd_hash)
                VALUES (?, ?, ?);
                """,
                (user_id, user_name, pwd_hash)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'User name "{user_name}" already taken.'
            )

    return {
        'message': 'New user created successfully.'
    }


@app.post('/login')
async def login(request: Request):
    helpers.check_mimetype(request, JSON_MIMETYPE)

    data = await helpers.get_json_data(request)
    user_name = data.get('user')
    pwd = data.get('password')

    if user_name is None or pwd is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Fields \'user\' or \'password\' missing from request body.'
        )

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT user_id, pwd_hash FROM user WHERE user_name=?;',
            (user_name,)
        )
        user_info = cur.fetchone()

    if user_info is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f'User with user_name={user_name} not found.'
        )

    user_id, pwd_hash = user_info
    if not bcrypt.checkpw(pwd.encode('UTF-8'), pwd_hash.encode('UTF-8')):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password.'
        )

    payload = {'user_id': user_id}
    token = jwt.encode(payload, SECRET_KEY, 'HS256')

    return {
        helpers.TOKEN_HEADER: token,
    }


@app.post('/todos')
async def create_todo(request: Request, token: str = Depends(header_scheme)):
    helpers.validate_token(token)
    helpers.check_mimetype(request, JSON_MIMETYPE)

    data = await helpers.get_json_data(request)
    todo = data.get('todo')

    if todo is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Field \'todo\' missing from request body.'
        )

    now = datetime.datetime.now()
    todo_id = helpers.get_last_id() + 1
    user_id = helpers.get_user_id(token)
    done = 0

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO todo VALUES (?, ?, ?, ?, ?)',
            (todo_id, todo, now, done, user_id)
        )
        conn.commit()

    resp = {
        'message': f'Todo item created with id={todo_id}'
    }

    return resp


@app.get('/todos')
async def get_all_todos(token: str = Depends(header_scheme)):
    helpers.validate_token(token)

    user_id = helpers.get_user_id(token)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM todo WHERE owner=?;',
            (user_id,)
        )
        todos = cur.fetchall()

    resp = []
    for todo in todos:
        todo_id, todo, created_at, done, owner = todo
        this_todo = {'todo_id': todo_id, 'todo': todo,
                     'created_at': created_at, 'done': bool(done)}
        resp.append(this_todo)

    return resp


@app.get('/todos/{todo_id}')
async def get_one_todo(todo_id: int, token: str = Depends(header_scheme)):
    helpers.validate_token(token)

    user_id = helpers.get_user_id(token)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT todo_id FROM todo WHERE owner=?;',
            (user_id,)
        )
        all_ids = cur.fetchall()
        if (todo_id,) not in all_ids:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f'Todo item with id={todo_id} not found.'
            )

        cur.execute(
            'SELECT * FROM todo WHERE todo_id=? AND owner=?;',
            (todo_id, user_id)
        )
        todo_id, todo, created_at, done, owner = cur.fetchone()

    resp = {'todo_id': todo_id, 'todo': todo,
            'created_at': created_at, 'done': bool(done)}

    return resp


@app.delete('/todos/{todo_id}')
async def delete_todo(todo_id: int, token: str = Depends(header_scheme)):
    helpers.validate_token(token)

    user_id = helpers.get_user_id(token)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT todo_id FROM todo WHERE owner=?;',
            (user_id,)
        )
        all_ids = cur.fetchall()
        if (todo_id,) not in all_ids:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f'Todo item with id={todo_id} not found.'
            )

        cur.execute(
            'DELETE FROM todo WHERE todo_id=? AND owner=?;',
            (todo_id, user_id)
        )
        conn.commit()

    return {
        'message': f'Todo item with id={todo_id} deleted.'
    }


@app.patch('/todos/{todo_id}')
async def modify_todo(
    todo_id: int, request: Request,
    token: str = Depends(header_scheme)
):
    helpers.validate_token(token)

    user_id = helpers.get_user_id(token)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT todo_id FROM todo WHERE owner=?;',
            (user_id,)
        )
        all_ids = cur.fetchall()

    if (todo_id,) not in all_ids:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f'Todo item with id={todo_id} not found.'
        )

    helpers.check_mimetype(request, JSON_MIMETYPE)
    data = await helpers.get_json_data(request)
    new_todo_text = data.get('todo')
    new_status = data.get('done')

    if new_status is None and new_todo_text is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Provide proper values for todo item.'
        )

    if new_status:
        new_status == 1

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if new_status is not None:
            cur.execute(
                'UPDATE todo SET done=? WHERE todo_id=? AND owner=?;',
                (new_status, todo_id, user_id)
            )
        if new_todo_text is not None:
            cur.execute(
                'UPDATE todo SET todo=? WHERE todo_id=? AND owner=?;',
                (new_todo_text, todo_id, user_id)
            )
        conn.commit()

    resp = {
        'message': f'Todo item with id={todo_id} updated.',
        'updated_todo': {
            'todo': new_todo_text,
            'done': bool(new_status),
        }
    }
    return resp
