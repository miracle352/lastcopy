FROM node:24.12.0-bookworm-slim AS node
FROM python:3.13.7-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY package.json package-lock.json ./
COPY web/package.json ./web/package.json
RUN npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build && useradd --uid 10001 --create-home lastcopy \
 && mkdir -p /app/private/container && chown -R lastcopy:lastcopy /app
USER lastcopy
ENV SAMPLE_MODE=true LASTCOPY_DATA_DIR=/app/private/container API_ORIGIN=http://127.0.0.1:8000 NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000 8000
CMD ["python", "-m", "scripts.container_start"]
