FROM python:3.12.2-slim-bullseye as base

## Install dependencies
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

## Build the app
FROM base as app

WORKDIR /app
COPY src/*.py /app/
