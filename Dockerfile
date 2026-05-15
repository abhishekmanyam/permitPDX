# ---- Stage 1: build the React frontend ----
FROM node:24-slim AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
ARG VITE_MAPBOX_TOKEN
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN
RUN npm run build

# ---- Stage 2: Python backend serving the API + built frontend ----
FROM python:3.12-slim AS app
WORKDIR /app

COPY apps/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend/ ./
COPY --from=web /web/dist ./web

ENV WEB_DIR=/app/web
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
