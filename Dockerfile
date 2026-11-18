# ---------- base: Python + libraries (cached between builds) ----------
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- train: retrain the model on the latest dataset ----------
FROM base AS train
ARG GIT_COMMIT=local
ENV GIT_COMMIT=${GIT_COMMIT}
COPY config.json train.py ./
COPY dataset/ ./dataset/
RUN python train.py

# ---------- test: run pytest against the freshly trained model ----------
FROM train AS test
RUN pip install --no-cache-dir pytest httpx
COPY app.py ./
COPY tests/ ./tests/
RUN python -m pytest -v tests

# ---------- runtime: the image that is deployed on EC2 ----------
FROM base AS runtime
COPY app.py config.json ./
COPY --from=train /app/artifacts ./artifacts
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
