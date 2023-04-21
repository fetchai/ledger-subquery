FROM onfinality/subql-node-cosmos:v1.19.1

# Add system dependencies
RUN apk update
RUN apk add postgresql14-client

# add extra tools that are required
ADD https://github.com/mikefarah/yq/releases/download/v4.26.1/yq_linux_amd64 /usr/local/bin/yq
RUN chmod +x /usr/local/bin/yq

WORKDIR /app

# install global dependencies
RUN npm install -g graphile-migrate

# add the dependencies
ADD ./package.json yarn.lock /app/
RUN yarn install --frozen-lockfile --prod

COPY ./.gmrc /app/.gmrc

ADD ./migrations /app/migrations
ADD ./proto /app/proto
ADD ./project.yaml schema.graphql /app/
ADD ./scripts/node-entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
