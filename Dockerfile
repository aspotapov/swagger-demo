FROM python:3.8.0-slim-buster

COPY . /app
RUN pip3 install -r /app/requirements.txt
WORKDIR /app
RUN python3 setup.py develop
ENTRYPOINT hierarchy
