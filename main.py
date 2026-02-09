import os
import json
import shutil
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# --- CONFIGURACIÓN DE DIRECTORIOS ---
# Creamos las carpetas si no existen
os.makedirs("retos", exist_ok=True)
os.makedirs("reportes", exist_ok=True)

# Servir archivos estáticos (imágenes en raíz)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Creamos la ruta completa a la carpeta static
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Nos aseguramos que la carpeta exista
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs("retos", exist_ok=True)
os.makedirs("reportes", exist_ok=True)

# Montamos usando la ruta absoluta
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Archivo maestro de retos (Metadata)
DB_CHALLENGES = "challenges.json"

# --- MODELOS DE DATOS ---

class StepEvidence(BaseModel):
    answer: str
    reasoning: str

class MissionSubmission(BaseModel):
    challenge_id: str
    student_name: str
    # Estructura rígida de 3 pasos como solicitaste
    step_1: StepEvidence
    step_2: StepEvidence
    step_3: StepEvidence
    timestamp: Optional[str] = None

class NewChallenge(BaseModel):
    id: str             # ej: "puente_colgante"
    title: str          # ej: "El Puente Colgante"
    desc: str           # ej: "Calcula tensores y resistencia"
    html_content: str   # El código HTML completo del reto

# --- FUNCIONES AUXILIARES ---

def load_challenges_meta():
    if os.path.exists(DB_CHALLENGES):
        with open(DB_CHALLENGES, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_challenges_meta(data):
    with open(DB_CHALLENGES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- RUTAS DE INTERFAZ (FRONTEND) ---

html_landing = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Construyendo a mis Ingenieras</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; }
        .hero-pattern { background-image: radial-gradient(#6366f1 0.5px, transparent 0.5px); background-size: 20px 20px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 50; }
        .modal.active { display: flex; }
    </style>
</head>
<body class="hero-pattern min-h-screen text-gray-800">

    <nav class="bg-white shadow-sm p-4 sticky top-0 z-40">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold text-indigo-700"><i class="fas fa-hard-hat"></i> Ingenieras</h1>
            <div class="space-x-4">
                <button onclick="openStudentModal()" class="text-sm font-semibold text-gray-600 hover:text-indigo-600"><i class="fas fa-user-graduate"></i> Mis Calificaciones</button>
                <button onclick="openAdminUpload()" class="text-sm font-semibold text-gray-600 hover:text-green-600"><i class="fas fa-plus-circle"></i> Cargar Reto</button>
                <button onclick="openAdminReports()" class="text-sm font-semibold text-gray-600 hover:text-blue-600"><i class="fas fa-clipboard-list"></i> Reportes</button>
            </div>
        </div>
    </nav>

    <div class="max-w-6xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-10 mt-6">
        
        <div class="space-y-6">
            <div class="bg-white p-2 rounded-xl shadow-lg ...">
                <img src="/static/img1.jpg" class="rounded-lg w-full h-64 object-cover" alt="Imagen 1">
            </div>

            <div class="bg-white p-2 rounded-xl shadow-lg ...">
                <img src="/static/img2.jpg" class="rounded-lg w-full h-64 object-cover" alt="Imagen 2">
            </div>
            <div class="text-center p-4">
                <h2 class="text-3xl font-extrabold text-gray-800">Hola, Ingeniera.</h2>
                <p class="text-gray-600 mt-2">"La ciencia de hoy es la tecnología del mañana."</p>
            </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl flex flex-col h-[600px] overflow-hidden border border-gray-100">
            <div class="bg-indigo-600 p-6 text-white">
                <h2 class="text-2xl font-bold">🚀 Misiones Activas</h2>
                <p class="text-indigo-200 text-sm">Desliza para ver retos anteriores</p>
            </div>
            <div id="challenges-list" class="flex-1 overflow-y-auto p-4 space-y-3 flex flex-col-reverse justify-end">
                </div>
        </div>
    </div>

    <div id="uploadModal" class="modal">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl p-6 relative">
            <button onclick="document.getElementById('uploadModal').classList.remove('active')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 text-2xl">&times;</button>
            <h2 class="text-2xl font-bold text-green-700 mb-4">🛠️ Crear Nuevo Reto</h2>
            
            <form onsubmit="submitNewChallenge(event)" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <input type="text" id="newId" placeholder="ID del reto (ej: puente_largo)" class="p-2 border rounded w-full font-mono text-sm" required>
                    <input type="text" id="newTitle" placeholder="Título (ej: El Puente)" class="p-2 border rounded w-full" required>
                </div>
                <input type="text" id="newDesc" placeholder="Descripción corta" class="p-2 border rounded w-full" required>
                
                <div>
                    <label class="block text-sm font-bold text-gray-600 mb-1">Código HTML (Debe incluir script de envío):</label>
                    <textarea id="newHtml" rows="10" class="w-full p-2 border rounded font-mono text-xs bg-gray-50" placeholder="<!DOCTYPE html>... Pega aquí el código del ejercicio. Asegúrate que envíe a /api/submit" required></textarea>
                </div>

                <div class="bg-yellow-50 p-3 rounded text-xs text-yellow-800">
                    <strong>Nota:</strong> El HTML debe tener un script que haga POST a <code>/api/submit</code> con la estructura JSON correcta (step_1, step_2, step_3).
                </div>

                <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded">PUBLICAR RETO</button>
            </form>
        </div>
    </div>

    <div id="studentModal" class="modal">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl p-6 relative">
            <button onclick="document.getElementById('studentModal').classList.remove('active')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 text-2xl">&times;</button>
            <h2 class="text-2xl font-bold text-indigo-700 mb-4">🎓 Mi Historial Académico</h2>
            
            <div class="flex gap-2 mb-4">
                <input type="text" id="studentSearchName" placeholder="Ingresa tu nombre exacto..." class="flex-1 p-2 border rounded">
                <button onclick="searchStudentHistory()" class="bg-indigo-600 text-white px-4 rounded hover:bg-indigo-700">Buscar</button>
            </div>

            <div id="studentHistoryResults" class="max-h-80 overflow-y-auto space-y-3">
                <p class="text-gray-500 text-center italic">Ingresa tu nombre para ver tus evidencias.</p>
            </div>
        </div>
    </div>

    <script>
        // 1. Cargar Retos al iniciar (ACTUALIZADO CON BOTÓN BORRAR)
        async function loadChallenges() {
            const res = await fetch('/api/challenges');
            const list = await res.json();
            const container = document.getElementById('challenges-list');
            container.innerHTML = "";
            
            if (list.length === 0) {
                container.innerHTML = "<p class='text-gray-400 text-center p-4'>No hay retos activos.</p>";
                return;
            }
            
            list.forEach(c => {
                // Creamos un contenedor relativo para posicionar el botón de borrar
                container.innerHTML += `
                    <div class="relative group">
                        <a href="/reto/${c.id}" class="block bg-gray-50 hover:bg-indigo-50 border-l-4 border-indigo-400 p-4 rounded-r shadow-sm transition transform hover:translate-x-1 pr-12">
                            <div class="flex justify-between">
                                <h3 class="font-bold text-gray-800">${c.title}</h3>
                                <span class="text-xs text-gray-500">${c.date || ''}</span>
                            </div>
                            <p class="text-sm text-gray-600">${c.desc}</p>
                        </a>
                        
                        <button onclick="deleteChallenge('${c.id}')" class="absolute top-2 right-2 text-gray-300 hover:text-red-500 p-2 transition z-10" title="Borrar Reto (Admin)">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
            });
        }
        loadChallenges();

        // --- NUEVA FUNCIÓN PARA BORRAR ---
        async function deleteChallenge(id) {
            // Evitamos que el clic en el botón active el enlace (opcional, manejado por posicionamiento, pero buena práctica)
            event.stopPropagation();
            event.preventDefault();

            // 1. Pedir confirmación y clave
            if (!confirm("¿Estás seguro de que quieres eliminar este reto permanentemente?")) return;
            
            const pwd = prompt("Ingresa la clave de ADMIN para confirmar el borrado:");
            if (!pwd) return;

            // 2. Llamar al backend
            const res = await fetch(`/api/delete_challenge/${id}?pwd=${pwd}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                alert("Reto eliminado correctamente.");
                loadChallenges(); // Recargar la lista visualmente
            } else {
                alert("Error: Clave incorrecta o fallo en el servidor.");
            }
        }

        // 2. Funciones Admin (Existentes...)
        function checkAdmin() {
            const pwd = prompt("Acceso Restringido. Clave:");
            return pwd === "admin";
        }

        function openAdminUpload() {
            if (checkAdmin()) document.getElementById('uploadModal').classList.add('active');
            else alert("Clave incorrecta");
        }

        function openAdminReports() {
            if (checkAdmin()) window.location.href = "/admin_panel?pwd=admin";
            else alert("Clave incorrecta");
        }

        function openStudentModal() {
            document.getElementById('studentModal').classList.add('active');
        }

        // 3. Lógica de Subida de Reto
        async function submitNewChallenge(e) {
            e.preventDefault();
            const payload = {
                id: document.getElementById('newId').value,
                title: document.getElementById('newTitle').value,
                desc: document.getElementById('newDesc').value,
                html_content: document.getElementById('newHtml').value
            };

            const res = await fetch('/api/create_challenge', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                alert("Reto creado exitosamente");
                window.location.reload();
            } else {
                alert("Error al crear el reto");
            }
        }

        // 4. Lógica de Historial Estudiante
        async function searchStudentHistory() {
            const name = document.getElementById('studentSearchName').value;
            if(!name) return;
            
            const res = await fetch(`/api/student_history?name=${name}`);
            const data = await res.json();
            const container = document.getElementById('studentHistoryResults');
            
            if (data.length === 0) {
                container.innerHTML = "<p class='text-red-500 text-center'>No se encontraron registros para este nombre.</p>";
                return;
            }

            let html = "";
            data.forEach(r => {
                html += `
                    <div class="border p-3 rounded bg-gray-50 text-sm">
                        <div class="flex justify-between font-bold text-indigo-700 mb-2">
                            <span>Reto: ${r.challenge_id}</span>
                            <span class="text-gray-400 font-normal text-xs">${r.timestamp}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-xs">
                            <div class="bg-white p-2 border rounded"><strong>P1:</strong> ${r.step_1.answer}</div>
                            <div class="bg-white p-2 border rounded"><strong>P2:</strong> ${r.step_2.answer}</div>
                            <div class="bg-white p-2 border rounded"><strong>P3:</strong> ${r.step_3.answer}</div>
                        </div>
                        <div class="mt-2 text-xs text-gray-500">
                            <strong>Razonamiento Final:</strong> "${r.step_3.reasoning}"
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
    </script>
</body>
</html>
"""

# HTML simplificado para el panel admin de reportes (sin cambios mayores)
html_admin_reports = """
<!DOCTYPE html>
<html><head><title>Reportes</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-100 p-8">
    <h1 class="text-2xl font-bold mb-4">📂 Archivo Central de Evidencias</h1>
    <a href="/" class="text-blue-600 underline mb-6 block">Volver</a>
    <div id="list" class="space-y-4"></div>
    <script>
        const pwd = new URLSearchParams(window.location.search).get('pwd');
        fetch('/api/all_reports?pwd='+pwd).then(r=>r.json()).then(data => {
            if(data.error) document.body.innerHTML = "Acceso Denegado";
            else {
                document.getElementById('list').innerHTML = data.map(r => `
                    <div class="bg-white p-4 shadow rounded">
                        <strong>${r.student_name}</strong> - <span class="text-blue-600">${r.challenge_id}</span>
                        <div class="text-xs text-gray-400">${r.timestamp}</div>
                        <details class="mt-2 text-sm"><summary class="cursor-pointer text-blue-500">Ver Detalles</summary>
                            <pre class="bg-gray-100 p-2 mt-2 whitespace-pre-wrap">${JSON.stringify(r, null, 2)}</pre>
                        </details>
                    </div>
                `).join('');
            }
        });
    </script>
</body></html>
"""

# --- ENDPOINTS (API) ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return html_landing

@app.get("/admin_panel", response_class=HTMLResponse)
async def admin_page(pwd: str):
    return html_admin_reports

@app.get("/api/challenges")
async def get_challenges():
    return load_challenges_meta()

# Endpoint para servir el HTML de un reto específico
@app.get("/reto/{challenge_id}")
async def serve_challenge(challenge_id: str):
    # Validar que no intenten salir del directorio (security)
    if ".." in challenge_id or "/" in challenge_id:
        raise HTTPException(400, "ID inválido")
    
    path = f"retos/{challenge_id}/index.html"
    if not os.path.exists(path):
        raise HTTPException(404, "Reto no encontrado. Verifica la carpeta.")
    return FileResponse(path)

# CREAR NUEVO RETO (Desde la Web)
@app.post("/api/create_challenge")
async def create_challenge(data: NewChallenge):
    # 1. Crear directorio
    dir_path = f"retos/{data.id}"
    os.makedirs(dir_path, exist_ok=True)
    
    # 2. Guardar HTML
    html_path = f"{dir_path}/index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(data.html_content)
    
    # 3. Actualizar metadatos
    meta = load_challenges_meta()
    # Revisar si ya existe para actualizar o agregar
    existing = next((item for item in meta if item["id"] == data.id), None)
    if existing:
        existing.update({
            "title": data.title,
            "desc": data.desc,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    else:
        meta.append({
            "id": data.id,
            "title": data.title,
            "desc": data.desc,
            "path": html_path,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    save_challenges_meta(meta)
    
    return {"status": "ok"}

# RECIBIR RESPUESTAS
@app.post("/api/submit")
async def submit_mission(submission: MissionSubmission):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    submission.timestamp = timestamp
    
    # Nombre de archivo seguro: fecha_nombre_reto.json
    safe_name = "".join(x for x in submission.student_name if x.isalnum())
    filename = f"reportes/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}_{submission.challenge_id}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        # Pydantic .json() está deprecado en v2, usamos model_dump_json o dict
        f.write(submission.json())
        
    return {"message": "Guardado correctamente"}

# CONSULTA ADMIN (Todos los reportes)
@app.get("/api/all_reports")
async def get_all_reports(pwd: str):
    if pwd != "admin":
        return {"error": "Unauthorized"}
    
    results = []
    # Escanear carpeta reportes
    files = sorted(os.listdir("reportes"), reverse=True) # Los más nuevos primero
    for filename in files:
        if filename.endswith(".json"):
            try:
                with open(f"reportes/{filename}", "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except:
                continue
    return results

# CONSULTA ESTUDIANTE (Por nombre)
@app.get("/api/student_history")
async def get_student_history(name: str):
    results = []
    # Escaneo simple (Para producción masiva se usaría base de datos real SQL)
    files = sorted(os.listdir("reportes"), reverse=True)
    
    query_name = name.lower().strip()
    
    for filename in files:
        if filename.endswith(".json"):
            try:
                with open(f"reportes/{filename}", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Comparación flexible (lowercase)
                    if query_name in data.get("student_name", "").lower():
                        results.append(data)
            except:
                continue
    return results

@app.delete("/api/delete_challenge/{challenge_id}")
async def delete_challenge(challenge_id: str, pwd: str):
    if pwd != "admin":
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    # 1. Eliminar de la lista JSON (Metadatos)
    meta = load_challenges_meta()
    
    # Filtramos la lista para excluir el ID que queremos borrar
    new_meta = [c for c in meta if c["id"] != challenge_id]
    
    if len(new_meta) == len(meta):
        raise HTTPException(status_code=404, detail="Reto no encontrado en la base de datos")
    
    save_challenges_meta(new_meta)
    
    # 2. Eliminar la carpeta física y sus archivos
    dir_path = f"retos/{challenge_id}"
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path) # Borra la carpeta y todo lo de adentro
        except Exception as e:
            # Si falla el borrado físico, avisamos pero no detenemos el proceso del JSON
            print(f"Error borrando carpeta: {e}")
            
    return {"status": "deleted", "id": challenge_id}

