#!/bin/sh

exec python -m hypercorn --bind 0.0.0.0:8000 src/app.asgi
