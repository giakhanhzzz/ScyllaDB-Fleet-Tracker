FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY frontend ./frontend
COPY database ./database
COPY scripts/wait_for_scylla.py ./scripts/wait_for_scylla.py
COPY simulator ./simulator
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
