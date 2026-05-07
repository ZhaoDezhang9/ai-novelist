# Backend Dockerfile — 多阶段构建 + 非 root 用户
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

RUN groupadd -r novelist && useradd -r -g novelist novelist

WORKDIR /app

COPY --from=builder /root/.local /home/novelist/.local
ENV PATH=/home/novelist/.local/bin:$PATH

COPY backend/ ./backend/
COPY .env.example ./

RUN mkdir -p /app/data /app/logs && chown -R novelist:novelist /app

USER novelist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
