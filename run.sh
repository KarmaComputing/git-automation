#!/bin/bash
. venv/bin/activate
cd src 
QUART_ENV=development QUART_DEBUG=1 python app.asgi
