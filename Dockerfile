FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Variables de entorno para configurar el servicio
ENV OLLAMA_URL=https://evaenespanol.loca.lt
ENV MODEL_NAME=llama3:8b
ENV PORT=5000

# Exponer el puerto
EXPOSE 5000

# Usar gunicorn como servidor WSGI para producción
CMD gunicorn --bind 0.0.0.0:$PORT app:app