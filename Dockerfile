FROM node:22-alpine AS miniapp
WORKDIR /app/miniapp
COPY miniapp/package.json miniapp/package-lock.json* ./
RUN npm install
COPY miniapp/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=miniapp /app/miniapp/dist ./miniapp/dist
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
