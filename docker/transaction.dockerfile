FROM python:3.9-slim-buster

# Install pipenv and compilation dependencies
RUN pip3 install cosmpy
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# add the remaining parts of the produce the build
COPY ./scripts/tx-entrypoint.py /app/tx-entrypoint.py

ENTRYPOINT ["python3"]
CMD ["/app/tx-entrypoint.py"]