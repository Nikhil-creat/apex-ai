FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Placeholder weights so the service boots. Replace with a trained model: python -m app.train
RUN python -c "from app.cnn_service import export; export()"
EXPOSE 8001
CMD ["uvicorn", "app.cnn_service:app", "--host", "0.0.0.0", "--port", "8001"]
