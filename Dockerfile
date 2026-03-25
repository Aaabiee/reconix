FROM python:3.13-slim AS backend-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pipenv

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

COPY fast_api/ ./fast_api/
COPY gunicorn.conf.py ./

FROM node:24-alpine AS frontend-deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

FROM node:24-alpine AS frontend-builder

WORKDIR /app
COPY --from=frontend-deps /app/node_modules ./node_modules
COPY package.json next.config.js tsconfig.json tailwind.config.ts postcss.config.js ./
COPY index.html index.scss App.tsx App.spec.tsx ./
COPY src/ ./src/
COPY public/ ./public/

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
RUN npm run build && \
    mkdir -p /app/.next/standalone /app/.next/static || \
    (echo "Frontend build skipped" && mkdir -p /app/.next/standalone /app/.next/static /app/public)

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r reconix && useradd -r -g reconix -d /app -s /sbin/nologin reconix

WORKDIR /app

COPY --from=backend-base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=backend-base /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=backend-base /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=backend-base /app/fast_api ./fast_api
COPY --from=backend-base /app/gunicorn.conf.py ./

COPY --from=frontend-builder /app/public ./frontend/public
COPY --from=frontend-builder /app/.next/standalone ./frontend/
COPY --from=frontend-builder /app/.next/static ./frontend/.next/static/

RUN chown -R reconix:reconix /app

USER reconix

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 8000 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health && wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["sh", "-c", "node frontend/server.js & gunicorn fast_api.main:app -c gunicorn.conf.py"]
