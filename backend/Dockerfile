FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Usamos la sintaxis de shell para que evalúe la variable $PORT de Render, si no existe usa 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
