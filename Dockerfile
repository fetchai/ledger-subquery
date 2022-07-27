FROM node:16-slim AS builder

RUN apt-get update && apt-get install -y tree

WORKDIR /app

# add the dependencies
ADD package.json yarn.lock /app/
RUN yarn install --frozen-lockfile

# add the remaining parts of the produce the build
COPY . /app
RUN yarn codegen && yarn build

FROM onfinality/subql-node-cosmos:v0.2.0

WORKDIR /app

# add the dependencies
ADD package.json yarn.lock /app/
RUN yarn install --frozen-lockfile --prod

COPY --from=builder /app/dist /app/dist
ADD proto /app/proto
ADD project.yaml schema.graphql /app/
