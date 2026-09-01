# syntax=docker/dockerfile:1.7
FROM node:24.15.0-alpine AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS dependencies
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS development
COPY --chown=node:node . .
RUN mkdir -p .next && chown node:node .next
USER node
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]

FROM dependencies AS check
COPY . .
CMD ["npm", "run", "check"]

FROM dependencies AS builder
COPY . .
ARG NEXT_PUBLIC_WOONLENS_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_WOONLENS_API_BASE_URL=${NEXT_PUBLIC_WOONLENS_API_BASE_URL}
RUN npm run build

FROM base AS runtime
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
