from flask import Flask, request, jsonify, render_template
import requests
import json
import os
import logging
from datetime import datetime, timedelta
from threading import Lock, Thread
import time
import schedule  # Importación explícita del módulo schedule
from flask_cors import CORS

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración de la API de Ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://evaenespanol.loca.lt")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3:8b")

# Contexto del sistema para Curiosity
ASSISTANT_CONTEXT = """
# Curiosity: Agente de Análisis de Competencia Especializado en IA Conversacional

## Rol Principal:
Eres Curiosity, un producto de Antares Innovate (www.antares.innovate.com), empresa líder en soluciones de IA conversacional. Como analista de inteligencia competitiva especializado, representas los valores de innovación, precisión y orientación estratégica que caracterizan a Antares Innovate. Tu objetivo es proporcionar análisis detallados y estratégicos del mercado.

## Objetivo Principal:
Realizar un análisis diario automatizado de los competidores directos e indirectos de Antares Innovate en el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales, enfocado en Estados Unidos y Colombia. Generar un informe ejecutivo con hallazgos estratégicos, comparaciones de precios, innovaciones detectadas y recomendaciones accionables.

## Instrucciones Detalladas:

### 1. Identificación de Competidores:
- Como un producto de Antares Innovate, tu misión es rastrear empresas competidoras en: Crunchbase, LinkedIn, G2, Capterra, SEMrush, TechCrunch, Product Hunt, AngelList.
- Monitorea foros como Reddit r/ArtificialIntelligence y comunidades de CX.
- Identifica competidores directos: Empresas con chatbots NLP avanzados, asistentes virtuales B2B, soluciones con modelos SaaS.
- Identifica competidores indirectos: Plataformas low-code que permitan crear chatbots básicos.
- Compara siempre con las soluciones propias de Antares Innovate, resaltando nuestras ventajas y áreas de oportunidad.

### 2. Monitoreo de Estrategias:
- Rastrea anuncios en Google Ads con palabras clave relevantes.
- Analiza campañas en LinkedIn, Facebook, Instagram y YouTube.
- Monitorea blogs y newsletters de competidores.
- Identifica lanzamientos de nuevas funcionalidades, tácticas de contenido y alianzas estratégicas.

### 3. Análisis de Precios:
- Evalúa estructuras de precios (suscripción vs. pago por uso).
- Compara costos por funcionalidades premium.
- Identifica descuentos para diferentes segmentos.

### 4. Detección de Innovaciones:
- Identifica nuevos modelos de IA implementados.
- Detecta mejoras en UX: dashboards, plantillas, soporte.
- Rastrea certificaciones obtenidas.

### 5. Formato del Informe Diario:
Debes generar un informe con la siguiente estructura, usando siempre la identidad y valores de Antares Innovate:

# Informe de Competencia - [Fecha]
## Powered by Antares Innovate - Líderes en Soluciones de IA Conversacional

## 1. Nuevos Competidores Detectados (Últimas 24h):
- **Nombre Empresa:** [Nombre]
  - País: [País]
  - Productos: [Descripción breve]
  - Precios: [Estructura de precios]
  - Diferenciador: [Propuesta de valor única]
  - **Comparación con Antares:** [Breve análisis comparativo]

## 2. Campañas Destacadas:
- **Empresa:** [Nombre]
  - Estrategia: [Descripción de la campaña]
  - Tácticas: [Tácticas específicas utilizadas]
  - **Efectividad estimada:** [Alta/Media/Baja]

## 3. Innovaciones Relevantes:
- **Tendencia Detectada:** [Descripción de tendencia]
- **Nueva Integración:** [Descripción de integración]
- **Posición de Antares:** [¿Cómo nos posicionamos frente a esta innovación?]

## 4. Comparativo de Precios (Top 5 Competidores vs. Antares Innovate):
| Empresa | Plan Básico | Plan Empresarial | Costo por Integración | Valor percibido |
|---------|-------------|-------------------|------------------------|-----------------|
| Antares Innovate | [Precio] | [Precio] | [Precio] | [Alto/Medio/Bajo] |
| [Competidor 1] | [Precio] | [Precio] | [Precio] | [Alto/Medio/Bajo] |

## 5. Recomendaciones para Antares Innovate:
- **Oportunidad:** [Descripción de oportunidad]
- **Alerta:** [Advertencia sobre amenaza competitiva]
- **Acción Sugerida:** [Recomendación específica]
- **Valor Añadido:** [Cómo esta acción mejorará nuestra posición competitiva]

Recuerda siempre:
1. Ser específico con datos concretos
2. Basar tus recomendaciones en evidencia
3. Proporcionar información accionable, no solo datos
4. Personalizar el informe para el contexto específico de Antares Innovate
5. Indicar claramente las fuentes de tus datos cuando sea posible
"""

# Almacenamiento de sesiones e informes
sessions = {}
sessions_lock = Lock()
daily_reports = []
daily_reports_lock = Lock()

def call_ollama_api(prompt, session_id, max_retries=3):
    """Llamar a la API de Ollama con reintentos"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construir el mensaje para la API
    messages = []
    
    # Preparar el contexto del sistema
    system_context = ASSISTANT_CONTEXT
    
    # Agregar el contexto del sistema como primer mensaje
    messages.append({
        "role": "system",
        "content": system_context
    })
    
    # Agregar historial de conversación si existe la sesión
    with sessions_lock:
        if session_id in sessions:
            messages.extend(sessions[session_id])
    
    # Agregar el nuevo mensaje del usuario
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Preparar los datos para la API
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    # Intentar con reintentos
    for attempt in range(max_retries):
        try:
            logger.info(f"Conectando a {OLLAMA_URL}...")
            response = requests.post(f"{OLLAMA_URL}/api/chat", headers=headers, json=data, timeout=120)
            
            # Si hay un error, intentar mostrar el mensaje
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    logger.error(f"Error detallado: {error_data}")
                except:
                    logger.error(f"Contenido del error: {response.text[:500]}")
                
                # Si obtenemos un 403, intentar con una URL alternativa
                if response.status_code == 403 and attempt == 0:
                    logger.info("Error 403, probando URL alternativa...")
                    alt_url = "http://127.0.0.1:11434/api/chat"
                    response = requests.post(alt_url, headers=headers, json=data, timeout=120)
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extraer la respuesta según el formato de Ollama
            if "message" in response_data and "content" in response_data["message"]:
                return response_data["message"]["content"]
            else:
                logger.error(f"Formato de respuesta inesperado: {response_data}")
                return "Lo siento, no pude generar una respuesta apropiada en este momento."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en intento {attempt+1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Retroceso exponencial
                logger.info(f"Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                return f"Lo siento, estoy experimentando problemas técnicos de comunicación. ¿Podríamos intentarlo más tarde?"
    
    return "No se pudo conectar al servicio. Por favor, inténtelo de nuevo más tarde."

def call_ollama_completion(prompt, session_id, max_retries=3):
    """Usar el endpoint de completion en lugar de chat (alternativa)"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construir prompt completo con contexto e historial
    full_prompt = ASSISTANT_CONTEXT + "\n\n"
    
    full_prompt += "Historial de conversación:\n"
    
    with sessions_lock:
        if session_id in sessions:
            for msg in sessions[session_id]:
                role = "Usuario" if msg["role"] == "user" else "Curiosity"
                full_prompt += f"{role}: {msg['content']}\n"
    
    full_prompt += f"\nUsuario: {prompt}\nCuriosity: "
    
    # Preparar datos para API de completion
    data = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    completion_url = f"{OLLAMA_URL}/api/generate"
    
    # Intentar con reintentos
    for attempt in range(max_retries):
        try:
            logger.info(f"Conectando a {completion_url}...")
            response = requests.post(completion_url, headers=headers, json=data, timeout=120)
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extraer respuesta del formato de completion
            if "response" in response_data:
                return response_data["response"]
            else:
                logger.error(f"Formato de respuesta inesperado: {response_data}")
                return "Lo siento, no pude generar una respuesta apropiada en este momento."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en intento {attempt+1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                return f"Lo siento, estoy experimentando problemas técnicos de comunicación. ¿Podríamos intentarlo más tarde?"
    
    return "No se pudo conectar al servicio. Por favor, inténtelo de nuevo más tarde."

def generate_daily_report():
    """Generar el informe diario de análisis de competencia"""
    logger.info("Generando informe diario de análisis de competencia...")
    
    report_request = f"""
    Como Curiosity, el agente de análisis competitivo creado por Antares Innovate (www.antares.innovate.com), genera un informe diario de análisis de competencia con fecha {datetime.now().strftime('%d-%m-%Y')}.
    
    Enfócate en:
    1. Nuevos competidores en el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales, comparándolos siempre con las soluciones de Antares Innovate.
    2. Campañas recientes destacadas de competidores conocidos, evaluando su efectividad y posible impacto.
    3. Innovaciones relevantes en el espacio de IA conversacional, analizando cómo posiciona esto a Antares Innovate en el mercado.
    4. Comparativo de precios actualizado entre los 5 competidores principales frente a Antares Innovate, incluyendo una valoración del valor percibido.
    5. Recomendaciones estratégicas específicas y accionables para que Antares Innovate mantenga y mejore su posición competitiva.
    
    Asegúrate de presentar a Antares Innovate en una luz favorable pero realista, destacando nuestras fortalezas y oportunidades de mejora.
    
    Usa el formato de informe detallado en tus instrucciones, con la identidad visual y de marca de Antares Innovate.
    """
    
    # ID de sesión específico para informes automáticos
    session_id = "daily_report_auto"
    
    try:
        # Primero intentar con el endpoint de chat
        report = call_ollama_api(report_request, session_id)
        
        # Si la respuesta está vacía, intentar con completion
        if not report or report.strip() == "":
            logger.info("El endpoint de chat no devolvió una respuesta, probando con completion...")
            report = call_ollama_completion(report_request, session_id)
    except Exception as e:
        logger.error(f"Error al generar informe diario: {e}")
        report = f"Error al generar informe diario: {str(e)}"
    
    # Almacenar el informe generado
    with daily_reports_lock:
        daily_reports.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": report
        })
        # Mantener solo los últimos 30 informes
        if len(daily_reports) > 30:
            daily_reports.pop(0)
    
    logger.info("Informe diario generado correctamente.")
    return report

def schedule_daily_reports():
    """Configurar la generación diaria de informes a las 7:00 AM"""
    # El módulo schedule ya está importado al inicio del archivo
    
    # Generar informe todos los días a las 7:00 AM
    schedule.every().day.at("07:00").do(generate_daily_report)
    
    # También generamos un informe a las 16:00 para tener actualizaciones 
    # de la segunda mitad del día (importante para el mercado de EE.UU.)
    schedule.every().day.at("16:00").do(generate_daily_report)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Comprobar cada minuto

@app.route('/')
def home():
    """Ruta de bienvenida básica con información de Antares Innovate"""
    return jsonify({
        "message": "Curiosity - Agente de Análisis de Competencia by Antares Innovate",
        "description": "Inteligencia competitiva automatizada para el mercado de chatbots, agentes virtuales y asistentes empresariales",
        "company": "Antares Innovate - Líderes en soluciones de IA conversacional",
        "status": "online",
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "/chat": "POST - Interactuar con Curiosity mediante mensajes",
            "/report": "GET - Obtener el último informe de análisis competitivo",
            "/reports": "GET - Listar todos los informes disponibles (últimos 30 días)",
            "/generate-report": "POST - Solicitar un nuevo análisis de mercado",
            "/reset": "POST - Reiniciar una sesión de conversación",
            "/health": "GET - Verificar estado del servicio"
        },
        "contact": "Para más información, visite www.antares.innovate.com"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para interactuar con el agente"""
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({"error": "Se requiere un 'message' en el JSON"}), 400
    
    # Obtener mensaje y session_id (crear uno nuevo si no se proporciona)
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    
    # Inicializar la sesión si es nueva
    with sessions_lock:
        if session_id not in sessions:
            sessions[session_id] = []
    
    # Obtener respuesta del asistente 
    try:
        # Primero intentar con el endpoint de chat
        response = call_ollama_api(message, session_id)
        
        # Si la respuesta está vacía, intentar con completion
        if not response or response.strip() == "":
            logger.info("El endpoint de chat no devolvió una respuesta, probando con completion...")
            response = call_ollama_completion(message, session_id)
    except Exception as e:
        logger.error(f"Error al obtener respuesta: {e}")
        logger.info("Probando con endpoint de completion alternativo...")
        response = call_ollama_completion(message, session_id)
    
    # Guardar la conversación en la sesión
    with sessions_lock:
        sessions[session_id].append({"role": "user", "content": message})
        sessions[session_id].append({"role": "assistant", "content": response})
    
    return jsonify({
        "response": response,
        "session_id": session_id
    })

@app.route('/report', methods=['GET'])
def get_latest_report():
    """Obtener el informe diario más reciente"""
    with daily_reports_lock:
        if not daily_reports:
            # Si no hay informes, generar uno
            report = generate_daily_report()
            return jsonify({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "content": report
            })
        else:
            # Devolver el informe más reciente
            return jsonify(daily_reports[-1])

@app.route('/reports', methods=['GET'])
def list_reports():
    """Listar todos los informes disponibles"""
    with daily_reports_lock:
        return jsonify({
            "count": len(daily_reports),
            "reports": daily_reports
        })

@app.route('/generate-report', methods=['POST'])
def force_report_generation():
    """Forzar la generación de un nuevo informe"""
    report = generate_daily_report()
    return jsonify({
        "message": "Informe generado correctamente",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": report
    })

@app.route('/reset', methods=['POST'])
def reset_session():
    """Reiniciar una sesión de conversación"""
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id] = []
            message = f"Sesión {session_id} reiniciada correctamente"
        else:
            message = f"La sesión {session_id} no existía, se ha creado una nueva"
            sessions[session_id] = []
    
    return jsonify({"message": message, "session_id": session_id})

@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del servicio con información adicional de Antares"""
    # Calcular tiempo desde el último informe generado
    last_report_time = None
    with daily_reports_lock:
        if daily_reports:
            try:
                last_report_time = datetime.strptime(daily_reports[-1]["date"], "%Y-%m-%d")
                time_since_last = (datetime.now() - last_report_time).total_seconds() / 3600
            except Exception as e:
                time_since_last = None
        else:
            time_since_last = None
    
    return jsonify({
        "status": "ok",
        "service_name": "Curiosity - Análisis de Competencia",
        "provider": "Antares Innovate",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_URL,
        "reports_count": len(daily_reports),
        "last_report_age_hours": time_since_last if time_since_last is not None else "N/A",
        "next_scheduled_report": "7:00 AM y 4:00 PM (hora del servidor)",
        "version": "1.2.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    # Iniciar el planificador de informes diarios en un hilo separado
    scheduler_thread = Thread(target=schedule_daily_reports)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Generar un informe inicial al iniciar la aplicación
    initial_report_thread = Thread(target=generate_daily_report)
    initial_report_thread.daemon = True
    initial_report_thread.start()
    
    # Obtener puerto de variables de entorno (para Render)
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0', port=port, debug=False)