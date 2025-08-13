import time

import httpx
import streamlit as st

API_URL = 'http://127.0.0.1:8000'
API_ACCESS_HEADER = 'X-Access-Token'
APP_NAME = 'Todo App'

st.set_page_config(page_title=APP_NAME, page_icon='📝')
st.title(APP_NAME)
if 'user_token' not in st.session_state:
    st.session_state['user_token'] = None
    st.session_state['user_name'] = None


def create_new_todo(new_todo: str) -> None:
    user_token = st.session_state['user_token']
    res = httpx.post(f'{API_URL}/todos',
                     headers={API_ACCESS_HEADER: user_token,
                              'Content-Type': 'application/json'},
                     json={'todo': new_todo})
    if res.is_success:
        st.toast('New task added.', icon='✅')
    else:
        st.error(res.json().get('detail'), icon='❌')


def toggle_todo_status(todo_id: int, current_status: bool) -> None:
    user_token = st.session_state['user_token']
    res = httpx.patch(f'{API_URL}/todos/{todo_id}',
                      headers={API_ACCESS_HEADER: user_token,
                               'Content-Type': 'application/json'},
                      json={'done': not current_status})
    if res.is_success:
        new_status = res.json().get('updated_todo').get('done')
        if new_status:
            st.toast('Task marked as done.', icon='✅')
        else:
            st.toast('Task marked as not done.', icon='✅')
    else:
        st.toast(res.json().get('detail'), icon='❌')


@st.dialog('Delete Task?')
def delete_todo(todo_id: int) -> None:
    with st.container(border=True):
        st.write('Are you sure you want to delete this task?')
        col1, col2 = st.columns([.2, 1])
        with col1:
            sure = st.button('Yes')
        with col2:
            cancel = st.button('Cancel', type='primary')
    if sure:
        user_token = st.session_state['user_token']
        res = httpx.delete(f'{API_URL}/todos/{todo_id}',
                           headers={API_ACCESS_HEADER: user_token})
        if res.is_success:
            st.toast('Task deleted.', icon='✅')
            st.rerun()
        else:
            st.toast(res.json().get('detail'), icon='❌')
    elif cancel:
        st.rerun()


@st.dialog('Edit Task')
def edit_todo(todo_id: int, current_text: str) -> None:
    user_token = st.session_state['user_token']
    with st.form('edit_todo'):
        new_text = st.text_input(
            'New text', value=current_text, label_visibility='hidden')
        edit_btn = st.form_submit_button('Edit')
        if edit_btn:
            res = httpx.patch(f'{API_URL}/todos/{todo_id}',
                              headers={API_ACCESS_HEADER: user_token},
                              json={'todo': new_text})
            if res.is_success:
                st.toast('Task edited.', icon='✅')
                st.rerun()
            else:
                st.error(res.json().get('detail'), icon='❌')


@st.dialog('Create New Account')
def signup() -> None:
    if st.session_state['user_token']:
        st.warning('Please log out of your current account to continue.')
        return
    with st.form('signup_form'):
        user = st.text_input('Username')
        pwd = st.text_input('Password', type='password')
        pwd_confirm = st.text_input('Confirm password', type='password')
        signup_btn = st.form_submit_button('Sign Up')
        if pwd != pwd_confirm:
            st.error('Passwords don\'t match.', icon='❌')
            return
        if signup_btn:
            res = httpx.post(f'{API_URL}/signup',
                             headers={'Content-Type': 'application/json'},
                             json={'user': user, 'password': pwd})
            if res.is_success:
                st.success('New user created successfully.', icon='✅')
                time.sleep(1)
                st.rerun()
            else:
                st.error(res.json().get('detail'), icon='❌')


@st.dialog('Log In to Your Account')
def login() -> None:
    if st.session_state['user_token']:
        st.warning('You\'re already logged in.', icon='⚠️')
        return
    with st.form('login_form'):
        user = st.text_input('Username')
        pwd = st.text_input('Password', type='password')
        login_btn = st.form_submit_button('Sign In')
        if login_btn:
            res = httpx.post(f'{API_URL}/login',
                             headers={'Content-Type': 'application/json'},
                             json={'user': user, 'password': pwd})
            if res.is_success:
                st.session_state['user_token'] = res.json().get(
                    API_ACCESS_HEADER)
                st.session_state['user_name'] = user
                st.success('Log in successful.', icon='✅')
                st.rerun()
            else:
                st.error(res.json().get('detail'), icon='❌')


def logout() -> None:
    if st.session_state['user_token'] is not None:
        st.session_state['user_token'] = None
        st.session_state['user_name'] = None
        st.success('Successfully logged out.', icon='✅')
    else:
        st.warning('You\'re already logged out.', icon='⚠️')


def render_top_buttons(user_token: str | None) -> None:
    if not user_token:
        col1, col2 = st.columns([.35, 2])
        col1.button('Log In', icon='👤', on_click=login)
        col2.button('Sign Up', icon='🆕', on_click=signup)
    else:
        st.button('Log Out', icon='⏏️', on_click=logout)


def render_new_task_section() -> None:
    st.subheader(f'Logged in as: {st.session_state['user_name']}')
    new_todo = st.text_input('Todo', label_visibility='hidden',
                             placeholder='Add task', icon='➕')
    if new_todo:
        create_new_todo(new_todo)
    st.divider()


def render_tasks_section(user_token: str) -> None:
    res = httpx.get(f'{API_URL}/todos',
                    headers={API_ACCESS_HEADER: user_token})
    if res.is_success:
        todos = res.json()
        with st.expander(f'Tasks ({len(todos)})', expanded=True, icon='📝'):
            if not todos:
                st.info('No tasks yet. Try adding some to see them here.')
                return

            filters = ['All', 'Done', 'Not done']
            filter = st.pills('Filters:', options=filters, default='All')
            filtered_todos = []
            match filter:
                case 'All':
                    filtered_todos = todos
                case 'Done':
                    filtered_todos = [
                        i for i in todos if i.get('done')]
                case 'Not done':
                    filtered_todos = [
                        i for i in todos if not i.get('done')]

            for todo_item in filtered_todos:
                todo_id = todo_item.get('todo_id')
                todo_text = todo_item.get('todo')
                todo_done = todo_item.get('done')
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, .1, .1])
                    with col1:
                        st.checkbox(todo_text,
                                    value=todo_done,
                                    key=f'checkbox-{todo_id}',
                                    on_change=toggle_todo_status,
                                    args=(todo_id, todo_done))
                    with col2:
                        st.button('🗑️', key=f'delete-btn-{todo_id}',
                                  on_click=delete_todo, args=(todo_id,))
                    with col3:
                        st.button('🖉', key=f'edit-btn-{todo_id}',
                                  on_click=edit_todo, args=(todo_id, todo_text))
    else:
        st.error(res.json().get('detail'), icon='❌')


user_token = st.session_state['user_token']
render_top_buttons(user_token)
if user_token:
    render_new_task_section()
    render_tasks_section(user_token)
else:
    st.info('Please log in to continue.\
        If you don\'t have an account try signing up.', icon='ℹ️')
