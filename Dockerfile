FROM 3.8.0-slim-buster

COPY . /app
RUN pip3 install -r /app/requirements.txt
RUN python3 /app/setup.py develop
ENTRYPOINT hierarchy