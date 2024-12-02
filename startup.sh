#!/bin/bash
python -m flask db upgrade
gunicorn --bind=0.0.0.0 --timeout 600 --workers 4 app:app
