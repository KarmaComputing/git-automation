#!/bin/sh

exec python -m hypercorn --bind 0.0.0.0:80 src/app.asgi
