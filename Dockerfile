FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Crear directorio de plantillas
RUN mkdir -p templates

# Exponer el puerto que usa la aplicación
EXPOSE 5000

# Variable de entorno para el puerto
ENV PORT=5000
ENV OLLAMA_URL=https://evaenespanol.loca.lt
ENV MODEL_NAME=neural-chat:7b

# Comando para ejecutar la aplicación con Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app:app