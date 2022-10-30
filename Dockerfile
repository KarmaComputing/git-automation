FROM python:3-alpine

ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password  --gecos "" -u 10001 quart

USER quart

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ./entrypoint.sh
