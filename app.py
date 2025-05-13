from flask import Flask, request, jsonify, render_template
import requests
import json
import os
import logging
from datetime import datetime
from threading import Lock
import time
import uuid
from flask_cors import CORS  # Importamos CORS para habilitar las solicitudes cross-origin

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(_name_)

app = Flask(_name_)
# Habilitar CORS para todas las rutas y orígenes
CORS(app, resources={r"/": {"origins": ""}})

# Configuración de la API de Ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://evaenespanol.loca.lt")
MODEL_NAME = os.environ.get("MODEL_NAME", "neural-chat:7b")

# Contexto del sistema para Curiosity - Actualizado para enfocarse en investigación y comparación
ASSISTANT_CONTEXT = """
# Curiosity: Agente de Investigación y Análisis Competitivo en IA Conversacional

## Rol Principal:
Eres Curiosity, un agente especializado en investigación de mercado y análisis competitivo para soluciones de IA conversacional. Tu misión es analizar otras empresas del sector, compararlas con Antares Innovate (www.antaresinnovate.com), e identificar oportunidades de mejora, elementos a implementar, y estrategias para destacar en el mercado.

## Objetivo Principal:
Proporcionar análisis detallados y estratégicos de competidores en el mercado de chatbots avanzados, agentes virtuales y asistentes empresariales, enfocados en Estados Unidos y Colombia. Tu objetivo es identificar tanto las fortalezas que debe emular Antares Innovate como las debilidades que debe evitar.

## Conocimiento sobre Antares Innovate:
Antares Innovate (www.antaresinnovate.com) es nuestra empresa de referencia para el análisis:
- Fundada en 2021, se especializa en soluciones de IA conversacional
- Su lema es "La Creatividad Mueve el Mundo; la Tecnología lo Acelera"
- Tiene presencia en Colombia y Estados Unidos
- Ofrece tres soluciones principales:
  1. Antares Virtual Assistant (AVA): Asistente virtual empresarial con capacidades multilingües
  2. Antares Business Intelligence (ABI): Plataforma para analizar interacciones de clientes
  3. Antares Integration Hub (AIH): Sistema para conectar chatbots con CRMs y sistemas empresariales

## Instrucciones para el Análisis:

### 1. Análisis de Competidores:
- Investiga competidores clave en el mercado de IA conversacional como Aivo, Botmaker, IBM Watson Assistant, Botpress, etc.
- Evalúa sus ofertas, modelo de negocio, propuesta de valor y diferenciales
- Compara objetivamente sus fortalezas y debilidades frente a Antares Innovate
- Identifica qué características, tácticas o estrategias debería adoptar Antares Innovate

### 2. Evaluación de Tendencias del Mercado:
- Identifica tendencias emergentes en IA conversacional como IA generativa, modelos de lenguaje, automatización avanzada
- Analiza cómo estas tendencias están influenciando a los líderes del mercado
- Recomienda cómo Antares Innovate puede aprovechar estas tendencias para diferenciarse

### 3. Benchmarking de Funcionalidades:
- Evalúa qué funcionalidades específicas destacan en los competidores
- Identifica qué características técnicas debería implementar Antares Innovate
- Compara integraciones, capacidades técnicas, UX y facilidad de uso

### 4. Análisis de Precios y Modelos de Negocio:
- Evalúa las estrategias de precios de los competidores (suscripción, pago por uso, freemium)
- Compara los planes y características incluidas en cada nivel
- Recomienda enfoques de precios y paquetización para Antares Innovate

### 5. Recomendaciones Estratégicas:
- Proporciona recomendaciones concretas, accionables y priorizadas
- Destaca oportunidades de mercado a corto y largo plazo
- Identifica nichos de mercado potenciales o sectores donde Antares Innovate podría especializarse

Cuando te soliciten analizar un competidor o tendencia específica, proporciona:
- Un análisis objetivo de sus fortalezas y debilidades
- Comparación directa con Antares Innovate
- Recomendaciones específicas sobre qué adoptar, mejorar o diferenciar
- Evaluación de la oportunidad/amenaza que representa

Recuerda que tu objetivo es ayudar a Antares Innovate a crear una estrategia competitiva superior, identificando lo mejor del mercado para implementarlo o mejorarlo, mientras se desarrollan diferenciadores únicos.
"""

# Almacenamiento de sesiones
sessions = {}
sessions_lock = Lock()

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

@app.route('/')
def home():
    """Ruta de bienvenida básica con información de Antares Innovate"""
    return jsonify({
        "message": "Curiosity - Agente de Investigación y Análisis Competitivo",
        "description": "Análisis de mercado y benchmarking para soluciones de IA conversacional",
        "company": "Antares Innovate - Líderes en soluciones de IA conversacional",
        "status": "online",
        "model": MODEL_NAME,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "/chat": "POST - Interactuar con Curiosity mediante mensajes",
            "/reset": "POST - Reiniciar una sesión de conversación",
            "/health": "GET - Verificar estado del servicio",
            # Mantenemos las mismas rutas para compatibilidad con el frontend, pero ahora devolverán respuestas mínimas
            "/report": "GET - Obtener el último informe (ruta mantenida para compatibilidad)",
            "/reports": "GET - Listar todos los informes (ruta mantenida para compatibilidad)",
            "/report/{id}": "GET - Obtener un informe específico (ruta mantenida para compatibilidad)",
            "/generate-report": "POST - Solicitar un nuevo análisis (ruta mantenida para compatibilidad)",
            "/competitors": "GET - Ver lista de competidores (ruta mantenida para compatibilidad)"
        },
        "contact": "Para más información, visite www.antaresinnovate.com"
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Endpoint para interactuar con el agente"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
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

@app.route('/reset', methods=['POST', 'OPTIONS'])
def reset_session():
    """Reiniciar una sesión de conversación"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
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

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Verificar estado del servicio con información adicional de Antares"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    return jsonify({
        "status": "ok",
        "service_name": "Curiosity - Agente de Investigación y Análisis",
        "provider": "Antares Innovate",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_URL,
        "active_sessions": len(sessions),
        "reports_count": 0,  # Siempre 0 ya que no hay informes
        "competitors_analyzed": 0,  # Siempre 0 ya que no hay competidores
        "last_report_age_hours": "N/A",  # No aplicable
        "last_competitor_update": "N/A",  # No aplicable
        "next_scheduled_report": "N/A",  # No aplicable
        "version": "1.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Rutas mantenidas para compatibilidad con el frontend pero con funcionalidad mínima
@app.route('/report', methods=['GET', 'OPTIONS'])
def get_latest_report():
    """Obtener el informe diario más reciente (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    return jsonify({
        "id": str(uuid.uuid4()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": "Esta funcionalidad no está disponible en esta versión. Por favor, use el chat para solicitar análisis de competidores o mercado."
    })

@app.route('/reports', methods=['GET', 'OPTIONS'])
def list_reports():
    """Listar todos los informes disponibles (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    return jsonify({
        "count": 0,
        "reports": []
    })

@app.route('/report/<report_id>', methods=['GET', 'OPTIONS'])
def get_report_by_id(report_id):
    """Obtener un informe específico por su ID (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    return jsonify({
        "id": report_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": "Esta funcionalidad no está disponible en esta versión. Por favor, use el chat para solicitar análisis de competidores o mercado."
    })

@app.route('/generate-report', methods=['POST', 'OPTIONS'])
def force_report_generation():
    """Forzar la generación de un nuevo informe (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    report_id = str(uuid.uuid4())
    return jsonify({
        "message": "Esta funcionalidad no está disponible en esta versión.",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "id": report_id,
        "content": "Por favor, use el chat para solicitar análisis específicos de competidores o del mercado."
    })

@app.route('/competitors', methods=['GET', 'OPTIONS'])
def list_competitors():
    """Listar competidores analizados (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    return jsonify({
        "count": 0,
        "competitors": []
    })

@app.route('/analyze-competitor', methods=['POST', 'OPTIONS'])
def analyze_competitor():
    """Analizar un competidor específico por su URL (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({"error": "Se requiere una 'url' en el JSON"}), 400
    
    url = data.get('url')
    
    return jsonify({
        "message": "Esta funcionalidad ha cambiado.",
        "competitor": {
            "name": "Nombre no disponible",
            "url": url,
            "analysis": "Por favor, use el chat para solicitar un análisis específico de este competidor, comparándolo con Antares Innovate."
        }
    })

@app.route('/custom-report', methods=['POST', 'OPTIONS'])
def generate_custom_report():
    """Generar un informe personalizado (mantenido para compatibilidad)"""
    # Manejo de solicitud OPTIONS para preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    report_id = str(uuid.uuid4())
    return jsonify({
        "message": "Esta funcionalidad no está disponible en esta versión.",
        "report_id": report_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": "Por favor, use el chat para solicitar análisis específicos de competidores, tendencias de mercado o recomendaciones estratégicas."
    })

@app.route('/web-interface')
def web_interface():
    """Interfaz web simple para interactuar con Curiosity"""
    return render_template('index.html')

if _name_ == '_main_':
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
    <title>Curiosity - Análisis de Mercado</title>
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
        .chat-container {
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
        input, button {
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
    </style>
</head>
<body>
    <header>
        <h1>Curiosity - Análisis Competitivo y de Mercado</h1>
        <p>Powered by Antares Innovate - La Creatividad Mueve el Mundo; la Tecnología lo Acelera.</p>
    </header>

    <div class="container">
        <div class="chat-container">
            <h2>Chat con Curiosity</h2>
            <div class="messages" id="messages"></div>
            <div>
                <input type="text" id="user-input" placeholder="Pregunta sobre competidores, mercado o recomendaciones estratégicas...">
                <button id="send-btn">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        // Variables para almacenar el ID de sesión
        let sessionId = session_${Date.now()};

        // Referencias a elementos del DOM
        const messagesContainer = document.getElementById('messages');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-btn');

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

        // Eventos
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Inicialización
        appendMessage('Hola, soy Curiosity, especialista en análisis competitivo y de mercado para soluciones de IA conversacional. Puedo ayudarte a comparar competidores con Antares Innovate, analizar tendencias del mercado y proporcionar recomendaciones estratégicas. ¿Sobre qué competidor o tendencia te gustaría saber más?', 'bot');
    </script>
</body>
</html>
            """)
    
    # Obtener puerto de variables de entorno (para Render)
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0', port=port, debug=False)