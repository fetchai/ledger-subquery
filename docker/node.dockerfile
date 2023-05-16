FROM node:16-slim AS builder

RUN apt-get update && apt-get install -y tree

WORKDIR /app

# Add build dependencies
ADD ./package.json yarn.lock /app/
RUN yarn install --frozen-lockfile

# Copy files & build
COPY . /app
RUN yarn codegen && yarn build

FROM onfinality/subql-node-cosmos:v1.19.1

# Add system dependencies
RUN apk update
RUN apk add postgresql14-client

# add extra tools that are required
ADD https://github.com/mikefarah/yq/releases/download/v4.26.1/yq_linux_amd64 /usr/local/bin/yq
RUN chmod +x /usr/local/bin/yq

WORKDIR /app

# add the dependencies
ADD ./package.json yarn.lock /app/
RUN yarn install --frozen-lockfile --prod

# include build artefacts in final image
COPY --from=builder /app/dist /app/dist

ADD ./proto /app/proto
ADD ./.gmrc /app/.gmrc
ADD ./project.yaml schema.graphql /app/
ADD ./scripts/node-entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
