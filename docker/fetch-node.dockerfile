FROM fetchai/fetchd:0.10.6

WORKDIR /app

COPY /scripts/fetch-node-entrypoint.sh /app/entrypoint.sh
RUN ["chmod", "+x", "/app/entrypoint.sh"]

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]