FROM python:3.9-slim-buster

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential libpq-dev postgresql-client

WORKDIR /app

# add the dependencies
COPY ./Pipfile Pipfile.lock /app/
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install

# add the remaining parts of the produce the build
COPY ./src/genesis/ /app/src/genesis/
ADD ./scripts/genesis.py /app/genesis.py
ADD ./scripts/genesis-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
