# Curiosity - Agente de Análisis de Competencia

Curiosity es un agente de inteligencia competitiva especializado en el análisis del mercado de IA conversacional. Desarrollado por Antares Innovate, este servicio proporciona análisis detallados y estratégicos de competidores, tendencias del mercado, comparación de precios y recomendaciones accionables.

## Características

- Análisis diario automatizado de competidores directos e indirectos
- Generación de informes ejecutivos detallados
- Monitoreo de estrategias de competidores
- Análisis de precios y estructuras de costos
- Detección de innovaciones en el mercado
- Chat interactivo para consultas específicas
- Interfaz web para visualización de informes

## Tecnología

- Backend: Flask (Python)
- Modelo de IA: neural-chat:7b via Ollama
- Análisis web: BeautifulSoup
- Programación de tareas: Schedule

## Instalación y Ejecución

### Usando Docker

1. Construye la imagen de Docker:
bash
docker build -t curiosity-agent .


2. Ejecuta el contenedor:
bash
docker run -p 5000:5000 curiosity-agent


### Usando Python directamente

1. Instala las dependencias:
bash
pip install -r requirements.txt


2. Ejecuta la aplicación:
bash
python app.py


### Variables de entorno

- OLLAMA_URL: URL del servicio Ollama (por defecto: "https://evaenespanol.loca.lt")
- MODEL_NAME: Nombre del modelo a utilizar (por defecto: "neural-chat:7b")
- PORT: Puerto en el que se ejecutará la aplicación (por defecto: 5000)

## Despliegue en Render

Este proyecto incluye un archivo render.yaml para facilitar el despliegue en la plataforma Render.

1. Crea un repositorio en GitHub con el código del proyecto
2. En Render, selecciona "Blueprint" y apunta al repositorio
3. Render configurará automáticamente el servicio según las especificaciones del archivo render.yaml

## Endpoints API

- GET /: Información general sobre el servicio
- POST /chat: Interactuar con Curiosity mediante mensajes
- GET /report: Obtener el último informe de análisis competitivo
- GET /reports: Listar todos los informes disponibles
- GET /report/{id}: Obtener un informe específico por su ID
- POST /generate-report: Solicitar un nuevo análisis de mercado
- POST /reset: Reiniciar una sesión de conversación
- GET /health: Verificar estado del servicio
- POST /analyze-competitor: Analizar un competidor específico por su URL
- POST /custom-report: Generar un informe personalizado
- GET /competitors: Ver lista de competidores analizados
- GET /web-interface: Interfaz web para interactuar con Curiosity

## Notas para los desarrolladores

- Los informes se generan automáticamente a las 7:00 AM y 4:00 PM (hora del servidor)
- Los datos de competidores se actualizan cada 6 horas
- Se recomienda personalizar la lista COMPETITORS_URLS en el código para añadir competidores relevantes

## Ejemplo de uso

python
import requests

# Interactuar con Curiosity
response = requests.post('http://localhost:5000/chat', json={
    'message': '¿Cuáles son las principales tendencias en IA conversacional para 2025?',
    'session_id': 'mi_sesion_123'
})

print(response.json()['response'])

# Generar un informe personalizado
response = requests.post('http://localhost:5000/custom-report', json={
    'focus_area': 'innovation',
    'industry': 'fintech',
    'region': 'latam'
})

print(response.json()['content'])
