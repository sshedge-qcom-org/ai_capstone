FROM node:22-alpine AS build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
RUN apk add --no-cache curl \
    && addgroup -g 10001 procurement \
    && adduser -D -u 10001 -G procurement procurement \
    && mkdir -p /srv /data /config \
    && chown -R procurement:procurement /srv /data /config
COPY --from=build /build/dist /srv
COPY deploy/Caddyfile /etc/caddy/Caddyfile
USER 10001:10001
EXPOSE 8443
