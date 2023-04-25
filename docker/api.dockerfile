FROM onfinality/subql-query:latest

COPY /scripts/api-entrypoint.sh /entrypoint.sh
RUN ["chmod", "+x", "./entrypoint.sh"]

ENTRYPOINT ["/bin/ash", "entrypoint.sh"]
CMD ["-f","/app"]