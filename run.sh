#!/usr/bin/bash

uv run fastapi dev & uv run streamlit run ui.py &
