# Curiosity: Agente de Análisis de Competencia para Antares Innovate

Curiosity es un agente virtual especializado en análisis de competencia para el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales virtuales. Diseñado específicamente para Antares Innovate, Curiosity realiza análisis diarios del mercado y genera informes estratégicos detallados.

## Características Principales

- **Análisis diario automatizado**: Genera un informe completo cada día a las 7:00 AM
- **Monitoreo de competidores**: Identifica y analiza competidores directos e indirectos
- **Análisis de estrategias**: Detecta campañas, promociones y tácticas de marketing de la competencia
- **Comparativa de precios**: Analiza y compara estructuras de precios y ofertas
- **Detección de innovaciones**: Identifica nuevas tendencias y mejoras tecnológicas
- **Recomendaciones estratégicas**: Proporciona sugerencias accionables para Antares Innovate

## Endpoints de la API

- **`/`**: Información general sobre la API
- **`/chat`**: Para interactuar con el agente mediante conversación
- **`/report`**: Obtener el informe diario más reciente
- **`/reports`**: Listar todos los informes disponibles (últimos 30 días)
- **`/generate-report`**: Forzar la generación de un nuevo informe
- **`/reset`**: Reiniciar una sesión de conversación
- **`/health`**: Verificar el estado del servicio

## Configuración

El servicio utiliza las siguientes variables de entorno:

- `OLLAMA_URL`: URL del servicio Ollama (por defecto: "https://evaenespanol.loca.lt")
- `MODEL_NAME`: Modelo a utilizar (por defecto: "llama3:8b")
- `PORT`: Puerto en el que se ejecutará el servicio (por defecto: 5000)

## Despliegue en Render

El repositorio incluye un archivo `render.yaml` para facilitar el despliegue en Render.com:

1. Crea una cuenta en Render.com
2. Conecta tu repositorio de GitHub
3. Haz clic en "New Web Service"
4. Selecciona "Blueprint" y elige este repositorio
5. Render detectará automáticamente la configuración del archivo render.yaml
6. Haz clic en "Create Service"

## Desarrollo Local

Para ejecutar el servicio localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (opcional)
export OLLAMA_URL=https://evaenespanol.loca.lt
export MODEL_NAME=llama3:8b

# Iniciar el servicio
python app.py
```

## Ejemplo de uso

### Interactuar con el agente

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Puedes analizar los competidores en el mercado de chatbots para atención al cliente?", "session_id": "usuario123"}'
```

### Obtener el último informe

```bash
curl -X GET http://localhost:5000/report
```

### Generar un nuevo informe

```bash
curl -X POST http://localhost:5000/generate-report
```

## Estructura del Informe

Los informes generados por Curiosity siguen esta estructura:

1. **Nuevos Competidores Detectados**: Empresas recientemente identificadas
2. **Campañas Destacadas**: Estrategias y tácticas de marketing relevantes
3. **Innovaciones Relevantes**: Tendencias tecnológicas y nuevas integraciones
4. **Comparativo de Precios**: Tabla comparativa de los principales competidores
5. **Recomendaciones para Antares Innovate**: Sugerencias estratégicas accionables

## Contribución

Para contribuir a este proyecto:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -m 'Añadir nueva funcionalidad'`)
4. Sube tus cambios (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request