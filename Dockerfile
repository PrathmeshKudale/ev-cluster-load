# ╔══════════════════════════════════════════════════════════════╗
# ║  GridFlow EV Cluster Load — Multi-stage Dockerfile           ║
# ║  Stage 1: build frontend (Node 20 alpine)                    ║
# ║  Stage 2: serve frontend with nginx                          ║
# ║  Stage 3: backend API (Python 3.12 slim)                     ║
# ╚══════════════════════════════════════════════════════════════╝

# ─── Stage 1: Frontend build ──────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline

COPY frontend/ ./

ARG VITE_API_BASE_URL=/api
ARG VITE_USE_MOCKS=false
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_USE_MOCKS=$VITE_USE_MOCKS

RUN npm run build

# ─── Stage 2: Nginx SPA server ────────────────────────────────
FROM nginx:1.27-alpine AS frontend

RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx/nginx.conf /etc/nginx/conf.d/app.conf
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

# ─── Stage 3: Backend API ─────────────────────────────────────
FROM python:3.12-slim AS backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

RUN useradd -m -u 1001 evuser && chown -R evuser:evuser /app
USER evuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
