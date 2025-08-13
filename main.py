import os
from datetime import datetime, timezone
from uuid import uuid4

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

import helpers
from db import get_db
from models import Todo, User

SECRET_KEY = os.getenv('SECRET_KEY')
JSON_MIMETYPE = helpers.JSON_MIMETYPE

load_dotenv()
app = FastAPI()
header_scheme = APIKeyHeader(name=helpers.TOKEN_HEADER)


@app.get('/')
def index():
    return {
        'detail': 'All good.'
    }


@app.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(request: Request, db: Session = Depends(get_db)):
    helpers.check_mimetype(request, JSON_MIMETYPE)
    data = await request.json()
    user_name = data.get('user')
    pwd = data.get('password')

    if user_name is None or pwd is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Fields 'user' or 'password' missing.")
    if len(pwd) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail='Password must be at least 8 characters long.')

    user_id = str(uuid4())
    pwd_hash = bcrypt.hashpw(pwd.encode(
        'UTF-8'), bcrypt.gensalt()).decode('UTF-8')

    if db.query(User).filter_by(user_name=user_name).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"User name '{user_name}' already taken.")
    db.add(User(id=user_id, user_name=user_name, pwd_hash=pwd_hash))
    db.commit()

    return {'detail': 'New user created successfully.'}


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    helpers.check_mimetype(request, JSON_MIMETYPE)
    data = await request.json()
    user_name = data.get('user')
    pwd = data.get('password')

    if user_name is None or pwd is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Fields 'user' or 'password' missing.")

    user = db.query(User).filter_by(user_name=user_name).first()

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail=f'User with {user_name=} not found.')

    if not bcrypt.checkpw(pwd.encode('UTF-8'), user.pwd_hash.encode('UTF-8')):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid username or password.')

    token = jwt.encode(
        {'user_id': user.id, 'last_pwd_change': user.last_pwd_change},
        SECRET_KEY, 'HS256')
    return {helpers.TOKEN_HEADER: token}


@app.post('/users/change-password')
async def change_password(request: Request, token: str = Depends(header_scheme), db: Session = Depends(get_db)):
    helpers.validate_token(token)
    helpers.check_mimetype(request)

    user_id = helpers.get_user_id(token)
    user = db.query(User).filter_by(id=user_id).first()

    # Verify old password
    data = await request.json()
    old_pwd = data.get('old_password')
    if not bcrypt.checkpw(old_pwd.encode('UTF-8'), user.pwd_hash.encode('UTF-8')):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid username or password.')

    new_pwd = data.get('new_password')
    if len(new_pwd) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail='Password must be at least 8 characters long.')
    # Hash and set new password
    user.pwd_hash = bcrypt.hashpw(new_pwd.encode(
        'UTF-8'), bcrypt.gensalt()).decode('UTF-8')
    user.last_pwd_change = datetime.now(timezone.utc).isoformat()
    db.commit()

    return {'detail': 'Password updated successfully.'}


@app.delete('/users/me')
async def delete_account(
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    user_id = helpers.get_user_id(token)
    user = db.query(User).filter_by(id=user_id).first()

    db.delete(user)
    db.commit()
    return {'detail': 'User deleted successfully.'}


@app.post('/todos', status_code=status.HTTP_201_CREATED)
async def create_todo(
    request: Request,
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    helpers.check_mimetype(request, JSON_MIMETYPE)
    data = await request.json()
    todo_text = data.get('todo')

    if todo_text is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Field 'todo' missing.")

    user_id = helpers.get_user_id(token)

    todo = Todo(todo=todo_text, done=False, owner=user_id)
    db.add(todo)
    db.commit()
    todo_id = todo.id

    return {'detail': f'Todo item created with id={todo_id}'}


@app.get('/todos')
async def get_all_todos(
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    user_id = helpers.get_user_id(token)

    todos = db.query(Todo).filter_by(owner=user_id).all()

    return [{'todo_id': t.id, 'todo': t.todo, 'created_at': t.created_at, 'done': bool(t.done)} for t in todos]


@app.get('/todos/{todo_id}')
async def get_one_todo(
    todo_id: int,
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    user_id = helpers.get_user_id(token)

    todo = db.query(Todo).filter_by(id=todo_id, owner=user_id).first()

    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f'Todo item with id={todo_id} not found.')

    return {'todo_id': todo.id, 'todo': todo.todo, 'created_at': todo.created_at, 'done': bool(todo.done)}


@app.delete('/todos/{todo_id}')
async def delete_todo(
    todo_id: int,
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    user_id = helpers.get_user_id(token)

    todo = db.query(Todo).filter_by(id=todo_id, owner=user_id).first()
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f'Todo item with id={todo_id} not found.')
    db.delete(todo)
    db.commit()

    return {'detail': f'Todo item with id={todo_id} deleted.'}


@app.patch('/todos/{todo_id}')
async def modify_todo(
    todo_id: int,
    request: Request,
    token: str = Depends(header_scheme),
    db: Session = Depends(get_db)
):
    helpers.validate_token(token)
    user_id = helpers.get_user_id(token)

    todo = db.query(Todo).filter_by(id=todo_id, owner=user_id).first()
    if not todo:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f'Todo item with id={todo_id} not found.')

    helpers.check_mimetype(request, JSON_MIMETYPE)
    data = await request.json()
    new_todo_text = data.get('todo')
    new_status = data.get('done')

    if new_status is None and new_todo_text is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail='Provide proper values for todo item.')

    if new_status is not None:
        todo.done = bool(new_status)
    if new_todo_text is not None:
        todo.todo = new_todo_text

    db.commit()

    return {
        'detail': f'Todo item with id={todo_id} updated.',
        'updated_todo': {
            'todo': new_todo_text if new_todo_text is not None else todo.todo,
            'done': bool(new_status) if new_status is not None else todo.done
        }
    }
