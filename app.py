from flask import Flask, request, jsonify, render_template
import requests
import json
import os
import logging
from datetime import datetime, timedelta
from threading import Lock, Thread
import time
import schedule
from flask_cors import CORS
import re
import random
from bs4 import BeautifulSoup
import traceback
import uuid

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
MODEL_NAME = os.environ.get("MODEL_NAME", "neural-chat:7b")  # Cambiado a neural-chat:7b

# URLs para análisis de competencia
COMPETITORS_URLS = [
    "https://www.aivo.co/",
    "https://botmaker.com/en/",
    "https://www.vozy.ai/en",
    "https://www.nerds.ai/en",
    "https://botpress.com",
    "https://www.cm.com/en-us/conversational-ai-cloud/",
    "https://www.tidio.com",
    "https://www.rezolve.ai",
    "https://clerk.chat",
    "https://denser.ai",
    "https://www.ibm.com/products/watsonx-assistant"
]

# Contexto del sistema para Curiosity
ASSISTANT_CONTEXT = """
# Curiosity: Agente de Análisis de Competencia Especializado en IA Conversacional

## Rol Principal:
Eres Curiosity, un producto de Antares Innovate (www.antaresinnovate.com), empresa líder en soluciones de IA conversacional. Como analista de inteligencia competitiva especializado, representas los valores de innovación, precisión y orientación estratégica que caracterizan a Antares Innovate. Tu objetivo es proporcionar análisis detallados y estratégicos del mercado.

## Objetivo Principal:
Realizar un análisis diario automatizado de los competidores directos e indirectos de Antares Innovate en el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales, enfocado en Estados Unidos y Colombia. Generar un informe ejecutivo con hallazgos estratégicos, comparaciones de precios, innovaciones detectadas y recomendaciones accionables.

## Conocimiento de Antares Innovate:
- Somos una empresa especializada en soluciones de IA conversacional fundada en 2021.
- Nuestras principales tecnologías incluyen: procesamiento de lenguaje natural (NLP) avanzado, aprendizaje automático, y asistentes virtuales multicanal.
- Nuestras principales soluciones son:
  1. Antares Virtual Assistant (AVA): Asistente virtual empresarial con capacidades multilingües
  2. Antares Business Intelligence (ABI): Plataforma para analizar interacciones de clientes
  3. Antares Integration Hub (AIH): Sistema para conectar chatbots con CRMs y sistemas empresariales

- Nuestras fortalezas principales son:
  * Personalización y adaptabilidad a necesidades específicas de cada industria
  * Integración perfecta con sistemas empresariales existentes
  * Capacidades multilingües avanzadas con especialización en español e inglés
  * Análisis de datos en tiempo real para optimizar decisiones empresariales
  * Escalabilidad para empresas de todos los tamaños

- Nuestros precios aproximados son:
  * Plan Básico: $500/mes (hasta 1,000 conversaciones)
  * Plan Empresarial: $2,000/mes (hasta 10,000 conversaciones)
  * Plan Enterprise: Personalizado ($5,000+/mes)

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
- Compara siempre con nuestras estructuras de precios de Antares Innovate.

### 4. Detección de Innovaciones:
- Identifica nuevos modelos de IA implementados.
- Detecta mejoras en UX: dashboards, plantillas, soporte.
- Rastrea certificaciones obtenidas.
- Evalúa la integración con sistemas empresariales existentes.
- Analiza la implementación de IA generativa y modelos LLM.

### 5. Formato del Informe Diario:
Debes generar un informe con la siguiente estructura, usando siempre la identidad y valores de Antares Innovate:

# Informe de Competencia - [Fecha]
## Powered by Antares Innovate - Líderes en Soluciones de IA Conversacional

## 1. Nuevos Competidores Detectados (Últimas 24h):
- *Nombre Empresa:* [Nombre]
  - País: [País]
  - Productos: [Descripción breve]
  - Precios: [Estructura de precios]
  - Diferenciador: [Propuesta de valor única]
  - *Comparación con Antares:* [Breve análisis comparativo]

## 2. Campañas Destacadas:
- *Empresa:* [Nombre]
  - Estrategia: [Descripción de la campaña]
  - Tácticas: [Tácticas específicas utilizadas]
  - *Efectividad estimada:* [Alta/Media/Baja]

## 3. Innovaciones Relevantes:
- *Tendencia Detectada:* [Descripción de tendencia]
- *Nueva Integración:* [Descripción de integración]
- *Posición de Antares:* [¿Cómo nos posicionamos frente a esta innovación?]

## 4. Comparativo de Precios (Top 5 Competidores vs. Antares Innovate):
| Empresa | Plan Básico | Plan Empresarial | Costo por Integración | Valor percibido |
|---------|-------------|-------------------|------------------------|-----------------|
| Antares Innovate | [Precio] | [Precio] | [Precio] | [Alto/Medio/Bajo] |
| [Competidor 1] | [Precio] | [Precio] | [Precio] | [Alto/Medio/Bajo] |

## 5. Recomendaciones para Antares Innovate:
- *Oportunidad:* [Descripción de oportunidad]
- *Alerta:* [Advertencia sobre amenaza competitiva]
- *Acción Sugerida:* [Recomendación específica]
- *Valor Añadido:* [Cómo esta acción mejorará nuestra posición competitiva]

Recuerda siempre:
1. Ser específico con datos concretos
2. Basar tus recomendaciones en evidencia
3. Proporcionar información accionable, no solo datos
4. Personalizar el informe para el contexto específico de Antares Innovate
5. Indicar claramente las fuentes de tus datos cuando sea posible

## 6. Tendencias del Mercado de IA Conversacional 2025:
Siempre debes incluir un análisis de las tendencias más recientes en el mercado, como:
- Implementación de Modelos de Lenguaje Grandes (LLM)
- Agentes autónomos basados en IA generativa
- Integración multicanal y omnicanal
- Analítica avanzada de conversaciones
- Personalización basada en datos del cliente
- IA conversacional para sectores específicos
"""

# Almacenamiento de sesiones e informes
sessions = {}
sessions_lock = Lock()
daily_reports = []
daily_reports_lock = Lock()
competitive_data = {}
competitive_data_lock = Lock()

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
            response = requests.post(f"{OLLAMA_URL}/api/chat", headers=headers, json=data, timeout=180)
            
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
                    response = requests.post(alt_url, headers=headers, json=data, timeout=180)
            
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
            response = requests.post(completion_url, headers=headers, json=data, timeout=180)
            
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

def fetch_competitor_data():
    """Obtener datos sobre competidores desde sus sitios web"""
    competitor_data = {}
    
    for url in COMPETITORS_URLS:
        try:
            # Extraer el dominio base para usarlo como identificador
            domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
            
            # Obtener el contenido del sitio web
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extraer título, descripción y texto relevante
                title = soup.title.string if soup.title else domain
                description = ""
                if soup.find('meta', attrs={'name': 'description'}):
                    description = soup.find('meta', attrs={'name': 'description'}).get('content', '')
                
                # Extraer textos relevantes (párrafos, headings, etc.)
                texts = []
                for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if tag.text and len(tag.text.strip()) > 20:  # Texto significativo
                        texts.append(tag.text.strip())
                
                # Filtrar textos para quedarnos con los más relevantes (máximo 10)
                relevant_texts = []
                for text in texts:
                    if any(keyword in text.lower() for keyword in ['ai', 'chatbot', 'conversational', 'assistant', 'virtual', 'automation']):
                        relevant_texts.append(text)
                
                if len(relevant_texts) > 10:
                    relevant_texts = relevant_texts[:10]
                
                # Guardar datos
                competitor_data[domain] = {
                    'url': url,
                    'title': title,
                    'description': description,
                    'texts': relevant_texts,
                    'last_update': datetime.now().strftime("%Y-%m-%d")
                }
                
                logger.info(f"Datos obtenidos de {domain}")
            else:
                logger.warning(f"No se pudo acceder a {url} - Código: {response.status_code}")
        except Exception as e:
            logger.error(f"Error al obtener datos de {url}: {str(e)}")
    
    return competitor_data

def update_competitive_data():
    """Actualizar datos competitivos de forma periódica"""
    try:
        logger.info("Actualizando datos de competidores...")
        data = fetch_competitor_data()
        
        with competitive_data_lock:
            global competitive_data
            competitive_data = data
        
        logger.info(f"Datos actualizados correctamente. {len(data)} competidores analizados.")
    except Exception as e:
        logger.error(f"Error al actualizar datos competitivos: {str(e)}")
        logger.error(traceback.format_exc())

def generate_competitor_prompt():
    """Generar un prompt con los datos de competidores para el informe"""
    with competitive_data_lock:
        if not competitive_data:
            return "No hay datos competitivos disponibles. Por favor, analiza el mercado basado en tu conocimiento."
        
        prompt = "Aquí tienes la información más reciente de algunos competidores importantes:\n\n"
        
        for domain, data in competitive_data.items():
            prompt += f"Competidor: {data['title']}\n"
            prompt += f"URL: {data['url']}\n"
            prompt += f"Descripción: {data['description']}\n"
            prompt += "Textos relevantes:\n"
            
            for i, text in enumerate(data['texts'], 1):
                # Limitar tamaño para no exceder contexto
                if len(text) > 300:
                    text = text[:300] + "..."
                prompt += f"{i}. {text}\n"
            
            prompt += "\n---\n\n"
        
        return prompt

def generate_daily_report():
    """Generar el informe diario de análisis de competencia"""
    logger.info("Generando informe diario de análisis de competencia...")
    
    # Actualizar datos competitivos antes de generar el informe
    update_competitive_data()
    
    # Preparar prompt con datos de competidores
    competitor_data_prompt = generate_competitor_prompt()
    
    report_request = f"""
    Como Curiosity, el agente de análisis competitivo creado por Antares Innovate (www.antaresinnovate.com), genera un informe diario de análisis de competencia con fecha {datetime.now().strftime('%d-%m-%Y')}.
    
    Utiliza la siguiente información sobre los competidores para elaborar un análisis preciso:
    
    {competitor_data_prompt}
    
    Enfócate en:
    1. Nuevos competidores en el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales, comparándolos siempre con las soluciones de Antares Innovate.
    2. Campañas recientes destacadas de competidores conocidos, evaluando su efectividad y posible impacto.
    3. Innovaciones relevantes en el espacio de IA conversacional, analizando cómo posiciona esto a Antares Innovate en el mercado.
    4. Comparativo de precios actualizado entre los 5 competidores principales frente a Antares Innovate, incluyendo una valoración del valor percibido.
    5. Recomendaciones estratégicas específicas y accionables para que Antares Innovate mantenga y mejore su posición competitiva.
    6. Tendencias actuales del mercado de IA conversacional en 2025.
    
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
            "id": str(uuid.uuid4()),
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
    # Generar informe todos los días a las 7:00 AM
    schedule.every().day.at("07:00").do(generate_daily_report)
    
    # También generamos un informe a las 16:00 para tener actualizaciones 
    # de la segunda mitad del día (importante para el mercado de EE.UU.)
    schedule.every().day.at("16:00").do(generate_daily_report)
    
    # Actualizar datos competitivos cada 6 horas
    schedule.every(6).hours.do(update_competitive_data)
    
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
        "model": MODEL_NAME,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "/chat": "POST - Interactuar con Curiosity mediante mensajes",
            "/report": "GET - Obtener el último informe de análisis competitivo",
            "/reports": "GET - Listar todos los informes disponibles (últimos 30 días)",
            "/report/{id}": "GET - Obtener un informe específico por su ID",
            "/generate-report": "POST - Solicitar un nuevo análisis de mercado",
            "/reset": "POST - Reiniciar una sesión de conversación",
            "/health": "GET - Verificar estado del servicio",
            "/competitors": "GET - Ver lista de competidores analizados"
        },
        "contact": "Para más información, visite www.antaresinnovate.com"
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
                "id": str(uuid.uuid4()),
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
            "reports": [{"id": r["id"], "date": r["date"]} for r in daily_reports]
        })

@app.route('/report/<report_id>', methods=['GET'])
def get_report_by_id(report_id):
    """Obtener un informe específico por su ID"""
    with daily_reports_lock:
        for report in daily_reports:
            if report["id"] == report_id:
                return jsonify(report)
        
        return jsonify({"error": "Informe no encontrado"}), 404

@app.route('/generate-report', methods=['POST'])
def force_report_generation():
    """Forzar la generación de un nuevo informe"""
    report = generate_daily_report()
    
    # Obtener el ID del informe recién generado
    report_id = None
    with daily_reports_lock:
        if daily_reports:
            report_id = daily_reports[-1]["id"]
    
    return jsonify({
        "message": "Informe generado correctamente",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "id": report_id,
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

@app.route('/competitors', methods=['GET'])
def list_competitors():
    """Listar competidores analizados"""
    with competitive_data_lock:
        competitors = []
        for domain, data in competitive_data.items():
            competitors.append({
                "name": data['title'],
                "url": data['url'],
                "description": data['description'],
                "last_update": data.get('last_update', 'N/A')
            })
        
        return jsonify({
            "count": len(competitors),
            "competitors": competitors
        })

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
    
    # Verificar estado de los datos competitivos
    competitors_count = 0
    last_competitor_update = "N/A"
    with competitive_data_lock:
        competitors_count = len(competitive_data)
        if competitive_data and next(iter(competitive_data.values())).get('last_update'):
            last_competitor_update = next(iter(competitive_data.values()))['last_update']
    
    return jsonify({
        "status": "ok",
        "service_name": "Curiosity - Análisis de Competencia",
        "provider": "Antares Innovate",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_URL,
        "reports_count": len(daily_reports),
        "competitors_analyzed": competitors_count,
        "last_report_age_hours": time_since_last if time_since_last is not None else "N/A",
        "last_competitor_update": last_competitor_update,
        "next_scheduled_report": "7:00 AM y 4:00 PM (hora del servidor)",
        "version": "2.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/analyze-competitor', methods=['POST'])
def analyze_competitor():
    """Analizar un competidor específico por su URL"""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({"error": "Se requiere una 'url' en el JSON"}), 400
    
    url = data.get('url')
    
    try:
        # Extraer el dominio base para usarlo como identificador
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
        
        # Obtener el contenido del sitio web
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return jsonify({"error": f"No se pudo acceder a la URL. Código: {response.status_code}"}), 400
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer título, descripción y texto relevante
        title = soup.title.string if soup.title else domain
        description = ""
        if soup.find('meta', attrs={'name': 'description'}):
            description = soup.find('meta', attrs={'name': 'description'}).get('content', '')
        
        # Extraer textos relevantes (párrafos, headings, etc.)
        texts = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if tag.text and len(tag.text.strip()) > 20:  # Texto significativo
                texts.append(tag.text.strip())
        
        # Filtrar textos para quedarnos con los más relevantes (máximo 10)
        relevant_texts = []
        for text in texts:
            if any(keyword in text.lower() for keyword in ['ai', 'chatbot', 'conversational', 'assistant', 'virtual', 'automation']):
                relevant_texts.append(text)
        
        if len(relevant_texts) > 10:
            relevant_texts = relevant_texts[:10]
        
        # Generar prompt para análisis
        analysis_prompt = f"""
        Analiza detalladamente este competidor potencial de Antares Innovate:
        
        Nombre/Título: {title}
        URL: {url}
        Descripción: {description}
        
        Textos relevantes del sitio web:
        {chr(10).join([f"- {text}" for text in relevant_texts])}
        
        Por favor proporciona:
        1. Resumen de sus productos/servicios principales
        2. Propuesta de valor única
        3. Fortalezas y debilidades en comparación con Antares Innovate
        4. Estimación de sus precios (si puedes inferirlos)
        5. Recomendaciones específicas para que Antares Innovate pueda diferenciarse o competir mejor
        
        Formato tu respuesta de manera clara y profesional.
        """
        
        # Generar análisis del competidor
        session_id = f"competitor_analysis_{domain}"
        analysis = call_ollama_api(analysis_prompt, session_id)
        
        # Guardar datos en la estructura de datos competitivos
        competitor_data = {
            'url': url,
            'title': title,
            'description': description,
            'texts': relevant_texts,
            'analysis': analysis,
            'last_update': datetime.now().strftime("%Y-%m-%d")
        }
        
        with competitive_data_lock:
            global competitive_data
            competitive_data[domain] = competitor_data
        
        return jsonify({
            "message": "Análisis de competidor completado",
            "competitor": {
                "name": title,
                "url": url,
                "analysis": analysis
            }
        })
        
    except Exception as e:
        logger.error(f"Error al analizar competidor: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error al analizar competidor: {str(e)}"}), 500

@app.route('/custom-report', methods=['POST'])
def generate_custom_report():
    """Generar un informe personalizado basado en criterios específicos"""
    data = request.json
    
    if not data:
        return jsonify({"error": "Se requiere un objeto JSON con los parámetros del informe"}), 400
    
    # Obtener parámetros del informe personalizado
    focus_area = data.get('focus_area', 'general')  # general, pricing, innovation, etc.
    competitors = data.get('competitors', [])  # Lista de competidores específicos
    industry = data.get('industry', 'general')  # Industria específica
    region = data.get('region', 'global')  # Región geográfica
    
    # Preparar prompt para el informe personalizado
    custom_prompt = f"""
    Como Curiosity, genera un informe personalizado de análisis competitivo para Antares Innovate con fecha {datetime.now().strftime('%d-%m-%Y')}.
    
    Parámetros específicos del informe:
    - Área de enfoque: {focus_area}
    - Competidores específicos: {', '.join(competitors) if competitors else 'Todos los competidores relevantes'}
    - Industria: {industry}
    - Región: {region}
    """
    
    # Añadir datos de competidores si están disponibles
    competitor_data_prompt = generate_competitor_prompt()
    if competitor_data_prompt:
        custom_prompt += f"\n\nInformación sobre competidores:\n{competitor_data_prompt}"
    
    # Añadir instrucciones específicas según el área de enfoque
    if focus_area == 'pricing':
        custom_prompt += """
        Enfócate especialmente en:
        1. Análisis detallado de estructuras de precios de los competidores
        2. Comparación con los precios de Antares Innovate
        3. Tendencias de precios en el mercado
        4. Recomendaciones para optimizar nuestra estrategia de precios
        """
    elif focus_area == 'innovation':
        custom_prompt += """
        Enfócate especialmente en:
        1. Últimas innovaciones tecnológicas de los competidores
        2. Tendencias emergentes en IA conversacional
        3. Oportunidades de innovación para Antares Innovate
        4. Recomendaciones para priorizar iniciativas de I+D
        """
    elif focus_area == 'marketing':
        custom_prompt += """
        Enfócate especialmente en:
        1. Estrategias de marketing de los competidores
        2. Canales de adquisición de clientes más efectivos
        3. Mensajes clave y propuestas de valor en el mercado
        4. Recomendaciones para mejorar el posicionamiento de Antares Innovate
        """
    
    # Generar el informe personalizado
    session_id = f"custom_report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        report = call_ollama_api(custom_prompt, session_id)
    except Exception as e:
        logger.error(f"Error al generar informe personalizado: {str(e)}")
        return jsonify({"error": f"Error al generar informe personalizado: {str(e)}"}), 500
    
    # Crear un ID único para el informe
    report_id = str(uuid.uuid4())
    
    # Almacenar el informe personalizado (opcional)
    with daily_reports_lock:
        daily_reports.append({
            "id": report_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": report,
            "type": "custom",
            "parameters": {
                "focus_area": focus_area,
                "competitors": competitors,
                "industry": industry,
                "region": region
            }
        })
    
    return jsonify({
        "message": "Informe personalizado generado correctamente",
        "report_id": report_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": report
    })

@app.route('/web-interface')
def web_interface():
    """Interfaz web simple para interactuar con Curiosity"""
    return render_template('index.html')

if __name__ == '_main_':
    # Crear directorio de plantillas si no existe
    os.makedirs('templates', exist_ok=True)
    
    # Crear una plantilla HTML simple si no existe
    template_path = os.path.join('templates', 'index.html')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curiosity - Antares Innovate</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        h1 {
            margin: 0;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .chat-container, .report-container {
            flex: 1;
            min-width: 300px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .messages {
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .user-message, .bot-message {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            max-width: 80%;
        }
        .user-message {
            background-color: #3498db;
            color: white;
            margin-left: auto;
        }
        .bot-message {
            background-color: #ecf0f1;
        }
        input, button, select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        input {
            width: 70%;
        }
        button {
            background-color: #2c3e50;
            color: white;
            cursor: pointer;
            border: none;
        }
        button:hover {
            background-color: #34495e;
        }
        .report-content {
            white-space: pre-wrap;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            height: 500px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <header>
        <h1>Curiosity - Agente de Análisis de Competencia</h1>
        <p>Powered by Antares Innovate - Líderes en Soluciones de IA Conversacional</p>
    </header>

    <div class="container">
        <div class="chat-container">
            <h2>Chat con Curiosity</h2>
            <div class="messages" id="messages"></div>
            <div>
                <input type="text" id="user-input" placeholder="Pregunta algo sobre el mercado de IA conversacional...">
                <button id="send-btn">Enviar</button>
            </div>
        </div>

        <div class="report-container">
            <h2>Informes de Análisis Competitivo</h2>
            <div>
                <button id="get-latest-report">Último Informe</button>
                <button id="generate-report">Generar Nuevo</button>
                <select id="report-select">
                    <option value="">-- Seleccionar informe --</option>
                </select>
            </div>
            <div class="loading" id="report-loading" style="display: none;">Cargando informe...</div>
            <div class="report-content" id="report-content"></div>
        </div>
    </div>

    <script>
        // Variables para almacenar el ID de sesión y los informes
        let sessionId = session_${Date.now()};
        let reports = [];

        // Referencias a elementos del DOM
        const messagesContainer = document.getElementById('messages');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-btn');
        const reportContent = document.getElementById('report-content');
        const reportLoading = document.getElementById('report-loading');
        const reportSelect = document.getElementById('report-select');
        const getLatestReportBtn = document.getElementById('get-latest-report');
        const generateReportBtn = document.getElementById('generate-report');

        // Función para enviar mensajes al chatbot
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            // Mostrar mensaje del usuario
            appendMessage(message, 'user');
            userInput.value = '';

            try {
                // Enviar solicitud al servidor
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message,
                        session_id: sessionId
                    })
                });

                if (!response.ok) {
                    throw new Error('Error en la comunicación con el servidor');
                }

                const data = await response.json();
                
                // Mostrar respuesta del chatbot
                appendMessage(data.response, 'bot');
            } catch (error) {
                console.error('Error:', error);
                appendMessage('Lo siento, ha ocurrido un error al procesar tu mensaje.', 'bot');
            }
        }

        // Función para añadir mensajes al contenedor
        function appendMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message';
            messageDiv.textContent = text;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Función para obtener el último informe
        async function getLatestReport() {
            reportLoading.style.display = 'block';
            reportContent.textContent = '';

            try {
                const response = await fetch('/report');
                if (!response.ok) {
                    throw new Error('Error al obtener el informe');
                }

                const data = await response.json();
                reportContent.textContent = data.content;
            } catch (error) {
                console.error('Error:', error);
                reportContent.textContent = 'Error al cargar el informe.';
            } finally {
                reportLoading.style.display = 'none';
            }
        }

        // Función para generar un nuevo informe
        async function generateReport() {
            reportLoading.style.display = 'block';
            reportContent.textContent = 'Generando informe... Esto puede tomar unos minutos.';

            try {
                const response = await fetch('/generate-report', {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Error al generar el informe');
                }

                const data = await response.json();
                reportContent.textContent = data.content;
                
                // Actualizar lista de informes
                await loadReports();
            } catch (error) {
                console.error('Error:', error);
                reportContent.textContent = 'Error al generar el informe.';
            } finally {
                reportLoading.style.display = 'none';
            }
        }

        // Función para cargar la lista de informes
        async function loadReports() {
            try {
                const response = await fetch('/reports');
                if (!response.ok) {
                    throw new Error('Error al obtener la lista de informes');
                }

                const data = await response.json();
                reports = data.reports;

                // Limpiar opciones actuales
                while (reportSelect.options.length > 1) {
                    reportSelect.remove(1);
                }

                // Añadir nuevas opciones
                reports.forEach(report => {
                    const option = document.createElement('option');
                    option.value = report.id;
                    option.textContent = Informe ${report.date};
                    reportSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error:', error);
            }
        }

        // Función para cargar un informe específico
        async function loadReport(reportId) {
            reportLoading.style.display = 'block';
            reportContent.textContent = '';

            try {
                const response = await fetch(/report/${reportId});
                if (!response.ok) {
                    throw new Error('Error al obtener el informe');
                }

                const data = await response.json();
                reportContent.textContent = data.content;
            } catch (error) {
                console.error('Error:', error);
                reportContent.textContent = 'Error al cargar el informe.';
            } finally {
                reportLoading.style.display = 'none';
            }
        }

        // Eventos
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        getLatestReportBtn.addEventListener('click', getLatestReport);
        generateReportBtn.addEventListener('click', generateReport);
        reportSelect.addEventListener('change', () => {
            const selectedId = reportSelect.value;
            if (selectedId) {
                loadReport(selectedId);
            }
        });

        // Inicialización
        appendMessage('Hola, soy Curiosity. ¿En qué puedo ayudarte hoy con el análisis competitivo?', 'bot');
        loadReports();
    </script>
</body>
</html>
            """)
    
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