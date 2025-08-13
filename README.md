# todo-fast

A simple **Todo Application** built with **FastAPI** for the backend and **Streamlit** for the frontend.  
The backend serves a REST API for managing todos and users, while the frontend provides a quick, minimal interface for interacting with the app.

## 🚀 Features

- **FastAPI** for blazing-fast API development
- **Streamlit** for a lightweight, interactive UI
- JWT-based authentication
- SQLite database using SQLAlchemy ORM
- Environment-based configuration

## 🛠 Running Locally

### 1. Prerequisites

Make sure you have Python **3.10+** installed.  
You will also need to set an environment variable for authentication:

```bash
export SECRET_KEY=your_secret_here
```

Or create a `.env` file with:

```env
SECRET_KEY=your_secret_here
```

### 2. Install Dependencies

We recommend using **uv** for dependency and virtual environment management — it’s fast and modern. You can find instructions on how to install uv using [their documentation](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Install all dependencies exactly as pinned in uv.lock
uv sync --frozen
```

To run commands inside the virtual environment without activating it:

```bash
uv run <command>
```

## ▶️ Running the App

Currently, the backend API and frontend UI are served on **different ports**:

- **FastAPI API** → [http://localhost:8000](http://localhost:8000)
- **Streamlit UI** → [http://localhost:8501](http://localhost:8501)

To run both together (janky but works):

```bash
uv run fastapi dev & uv run streamlit run ui.py &
```

💡 **Better solution?**  
Eventually, this will likely be handled via:

- **Docker Compose** for orchestrating multiple services
- Or running Streamlit as a subpath behind FastAPI with reverse proxying

## 🐳 Docker Support

A `Dockerfile` will be added in the future to streamline deployment.

## 📌 Notes & Warnings

- **SECRET_KEY** must be set before starting the app — either in `.env` or via `export`.
- This project is for learning/demo purposes. Not production-hardened yet.
