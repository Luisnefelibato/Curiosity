FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos de la aplicación
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto donde se ejecutará la aplicación
EXPOSE 5000

# Variable de entorno para evitar que Flask cree un archivo .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Variable de entorno para que Flask sepa que debe ejecutarse en modo producción
ENV FLASK_ENV production
# Variable de entorno para Python para usar UTF-8 como encoding por defecto
ENV PYTHONIOENCODING UTF-8

# Definir variables de entorno para la aplicación
ENV OLLAMA_URL https://evaenespanol.loca.lt
ENV MODEL_NAME neural-chat:7b
ENV PORT 5000

# Comando para iniciar la aplicación
CMD gunicorn --bind 0.0.0.0:$PORT app:app