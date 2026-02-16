import os
import json
import shutil
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import random

app = FastAPI()

# --- CONFIGURACIÓN DE DIRECTORIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs("retos", exist_ok=True)
os.makedirs("reportes", exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
DB_CHALLENGES = "challenges.json"

# --- MODELOS DE DATOS (ACTUALIZADOS PARA SER DINÁMICOS) ---

class StepEvidence(BaseModel):
    question_id: str  # Ej: "Paso 1", "Paso 2"
    answer: str
    reasoning: str

class MissionSubmission(BaseModel):
    challenge_id: str
    student_name: str
    steps: List[StepEvidence]  # Lista dinámica que soporta de 1 a N pasos
    timestamp: Optional[str] = None

class NewChallenge(BaseModel):
    id: str
    title: str
    desc: str
    html_content: str

# --- FUNCIONES AUXILIARES ---

def load_challenges_meta():
    if os.path.exists(DB_CHALLENGES):
        try:
            with open(DB_CHALLENGES, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
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
            <div class="bg-white p-2 rounded-xl shadow-lg flex justify-center items-center bg-gray-50 h-64">
				<img id="random-img-1" src="" class="rounded-lg w-full h-full object-cover hidden" alt="Foto STEM 1">
				<i id="loader-img-1" class="fas fa-spinner fa-spin text-indigo-300 text-3xl"></i>
			</div>
			<div class="bg-white p-2 rounded-xl shadow-lg flex justify-center items-center bg-gray-50 h-64">
				<img id="random-img-2" src="" class="rounded-lg w-full h-full object-cover hidden" alt="Foto STEM 2">
				<i id="loader-img-2" class="fas fa-spinner fa-spin text-indigo-300 text-3xl"></i>
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
            <div id="challenges-list" class="flex-1 overflow-y-auto p-4 space-y-3 flex flex-col-reverse justify-end"></div>
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
                    <label class="block text-sm font-bold text-gray-600 mb-1">Código HTML generado por la Gema:</label>
                    <textarea id="newHtml" rows="10" class="w-full p-2 border rounded font-mono text-xs bg-gray-50" placeholder="Pega aquí el código del ejercicio..." required></textarea>
                </div>
                <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded">PUBLICAR RETO</button>
            </form>
        </div>
    </div>

    <div id="studentModal" class="modal">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl p-6 relative max-h-[90vh] flex flex-col">
            <button onclick="document.getElementById('studentModal').classList.remove('active')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 text-2xl">&times;</button>
            <h2 class="text-2xl font-bold text-indigo-700 mb-4">🎓 Mi Historial Académico</h2>
            <div class="flex gap-2 mb-4">
                <input type="text" id="studentSearchName" placeholder="Ingresa tu nombre exacto..." class="flex-1 p-2 border rounded">
                <button onclick="searchStudentHistory()" class="bg-indigo-600 text-white px-4 rounded hover:bg-indigo-700">Buscar</button>
            </div>
            <div id="studentHistoryResults" class="overflow-y-auto flex-1 space-y-4 pr-2">
                <p class="text-gray-500 text-center italic">Ingresa tu nombre para ver tus evidencias.</p>
            </div>
        </div>
    </div>

    <script>
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

        async function deleteChallenge(id) {
            event.stopPropagation();
            event.preventDefault();
            if (!confirm("¿Estás seguro de que quieres eliminar este reto permanentemente?")) return;
            const pwd = prompt("Ingresa la clave de ADMIN para confirmar el borrado:");
            if (!pwd) return;

            const res = await fetch(`/api/delete_challenge/${id}?pwd=${pwd}`, { method: 'DELETE' });
            if (res.ok) {
                alert("Reto eliminado correctamente.");
                loadChallenges();
            } else alert("Error: Clave incorrecta o fallo en el servidor.");
        }

        function checkAdmin() {
            const pwd = prompt("Acceso Restringido. Clave:");
            if(pwd === "admin") {
                sessionStorage.setItem("admin_pwd", pwd);
                return true;
            }
            return false;
        }

        function openAdminUpload() {
            if (sessionStorage.getItem("admin_pwd") === "admin" || checkAdmin()) document.getElementById('uploadModal').classList.add('active');
            else alert("Clave incorrecta");
        }

        function openAdminReports() {
            if (sessionStorage.getItem("admin_pwd") === "admin" || checkAdmin()) window.location.href = "/admin_panel?pwd=admin";
            else alert("Clave incorrecta");
        }

        function openStudentModal() {
            document.getElementById('studentModal').classList.add('active');
        }

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
            } else alert("Error al crear el reto");
        }

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
                let stepsHtml = "";
                if (r.steps && Array.isArray(r.steps)) {
                    // Renderizado dinámico de N pasos
                    stepsHtml = r.steps.map(s => `
                        <div class="bg-white p-3 border rounded shadow-sm">
                            <strong class="text-indigo-700">${s.question_id}:</strong> ${s.answer}
                            <div class="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded border border-dashed border-gray-200">
                                <em>Razón:</em> ${s.reasoning}
                            </div>
                        </div>
                    `).join('');
                } else {
                    stepsHtml = `<p class="text-red-500 text-xs">Formato de evidencia antiguo o incompatible.</p>`;
                }

                html += `
                    <div class="border p-4 rounded-lg bg-gray-50 shadow-sm mb-4">
                        <div class="flex justify-between font-bold text-gray-800 mb-3 border-b pb-2">
                            <span>Misión: <span class="text-indigo-600">${r.challenge_id}</span></span>
                            <span class="text-gray-400 font-normal text-xs"><i class="far fa-clock"></i> ${r.timestamp}</span>
                        </div>
                        <div class="space-y-2">
                            ${stepsHtml}
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        async function loadRandomImages() {
			try {
				const res = await fetch('/api/random_images');
				const data = await res.json();
				
				if (data.images && data.images.length >= 2) {
				    const img1 = document.getElementById('random-img-1');
				    const img2 = document.getElementById('random-img-2');
				    
				    img1.src = '/static/' + data.images[0];
				    img2.src = '/static/' + data.images[1];
				    
				    // Mostrar imágenes y ocultar los spinners de carga
				    img1.onload = () => { img1.classList.remove('hidden'); document.getElementById('loader-img-1').classList.add('hidden'); };
				    img2.onload = () => { img2.classList.remove('hidden'); document.getElementById('loader-img-2').classList.add('hidden'); };
				}
			} catch (e) {
				console.error("Error cargando imágenes aleatorias:", e);
			}
		}

		// Ejecutar al cargar la página
		loadRandomImages();
    </script>
</body>
</html>
"""

html_admin_reports = """
<!DOCTYPE html>
<html><head><title>Reportes | Admin</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-8 min-h-screen">
    <div class="max-w-5xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-gray-800"><i class="fas fa-folder-open text-blue-600"></i> Archivo Central de Evidencias</h1>
            <a href="/" class="bg-white text-gray-600 px-4 py-2 rounded shadow hover:text-blue-600 transition"><i class="fas fa-arrow-left"></i> Volver al Inicio</a>
        </div>
        <div id="list" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
    </div>
    
    <script>
        const pwd = new URLSearchParams(window.location.search).get('pwd');
        
        function loadReports() {
            fetch('/api/all_reports?pwd='+pwd).then(r=>r.json()).then(data => {
                if(data.error) {
                    document.body.innerHTML = "<h2 class='text-red-500 text-center text-2xl mt-20'>Acceso Denegado</h2>";
                } else if(data.length === 0) {
                    document.getElementById('list').innerHTML = "<p class='text-gray-500'>No hay reportes guardados.</p>";
                } else {
                    document.getElementById('list').innerHTML = data.map(r => `
                        <div class="bg-white p-5 shadow-lg rounded-xl border border-gray-200 relative">
                            <button onclick="deleteReport('${r.filename}')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 transition" title="Borrar Reporte">
                                <i class="fas fa-trash"></i>
                            </button>
                            <h3 class="text-xl font-bold text-gray-800 border-b pb-2 mb-2">${r.student_name}</h3>
                            <p class="text-sm font-semibold text-blue-600 mb-1">Reto: ${r.challenge_id}</p>
                            <div class="text-xs text-gray-500 mb-3"><i class="far fa-calendar-alt"></i> ${r.timestamp}</div>
                            
                            <details class="text-sm group">
                                <summary class="cursor-pointer text-blue-500 font-semibold hover:text-blue-700 outline-none">Ver Detalles del Ejercicio</summary>
                                <div class="bg-gray-50 p-3 mt-2 rounded border border-gray-200 space-y-2 max-h-60 overflow-y-auto">
                                    ${r.steps ? r.steps.map(s => `
                                        <div>
                                            <span class="font-bold text-gray-700">${s.question_id}:</span> <span class="text-green-700 font-mono">${s.answer}</span>
                                            <p class="text-xs text-gray-500 italic mt-1">"${s.reasoning}"</p>
                                        </div>
                                    `).join('<hr class="my-2 border-gray-200">') : '<span class="text-red-400">Datos antiguos o corruptos</span>'}
                                </div>
                            </details>
                        </div>
                    `).join('');
                }
            });
        }
        
        async function deleteReport(filename) {
            if(!confirm("¿Borrar este reporte de estudiante permanentemente?")) return;
            const res = await fetch(`/api/delete_report/${filename}?pwd=${pwd}`, { method: 'DELETE' });
            if(res.ok) {
                loadReports();
            } else {
                alert("Error al borrar el reporte.");
            }
        }

        loadReports();
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

@app.get("/reto/{challenge_id}")
async def serve_challenge(challenge_id: str):
    if ".." in challenge_id or "/" in challenge_id:
        raise HTTPException(400, "ID inválido")
    
    path = f"retos/{challenge_id}/index.html"
    if not os.path.exists(path):
        raise HTTPException(404, "Reto no encontrado. Verifica la carpeta.")
    return FileResponse(path)

@app.post("/api/create_challenge")
async def create_challenge(data: NewChallenge):
    dir_path = f"retos/{data.id}"
    os.makedirs(dir_path, exist_ok=True)
    
    html_path = f"{dir_path}/index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(data.html_content)
    
    meta = load_challenges_meta()
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

@app.post("/api/submit")
async def submit_mission(submission: MissionSubmission):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    submission.timestamp = timestamp
    
    # Sanitización estricta del nombre para el archivo
    safe_name = "".join(x for x in submission.student_name if x.isalnum() or x.isspace()).strip().replace(" ", "_")
    if not safe_name:
        safe_name = "estudiante_anonimo"
        
    filename = f"reportes/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}_{submission.challenge_id}.json"
    
    # IMPORTANTE: Usamos model_dump() y json.dump con ensure_ascii=False para evitar corrupción de datos
    with open(filename, "w", encoding="utf-8") as f:
        # En Pydantic v2 es model_dump(). Si usas v1, cámbialo a submission.dict()
        json.dump(submission.model_dump(), f, ensure_ascii=False, indent=4)
        
    return {"message": "Guardado correctamente"}

@app.get("/api/all_reports")
async def get_all_reports(pwd: str):
    if pwd != "admin":
        return {"error": "Unauthorized"}
    
    results = []
    files = sorted(os.listdir("reportes"), reverse=True)
    for filename in files:
        if filename.endswith(".json"):
            try:
                with open(f"reportes/{filename}", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["filename"] = filename # Inyectamos el nombre de archivo para poder borrarlo
                    results.append(data)
            except Exception as e:
                print(f"Error leyendo {filename}: {e}")
                continue
    return results

@app.get("/api/student_history")
async def get_student_history(name: str):
    results = []
    files = sorted(os.listdir("reportes"), reverse=True)
    query_name = name.lower().strip()
    
    for filename in files:
        if filename.endswith(".json"):
            try:
                with open(f"reportes/{filename}", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if query_name in data.get("student_name", "").lower():
                        results.append(data)
            except Exception:
                continue
    return results

@app.delete("/api/delete_challenge/{challenge_id}")
async def delete_challenge(challenge_id: str, pwd: str):
    if pwd != "admin":
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    meta = load_challenges_meta()
    new_meta = [c for c in meta if c["id"] != challenge_id]
    
    if len(new_meta) == len(meta):
        raise HTTPException(status_code=404, detail="Reto no encontrado en la base de datos")
    
    save_challenges_meta(new_meta)
    
    dir_path = f"retos/{challenge_id}"
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
        except Exception as e:
            print(f"Error borrando carpeta: {e}")
            
    return {"status": "deleted", "id": challenge_id}

# --- NUEVO ENDPOINT PARA BORRAR REPORTES DE ESTUDIANTES ---
@app.delete("/api/delete_report/{filename}")
async def delete_report(filename: str, pwd: str):
    if pwd != "admin":
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    # Medida de seguridad básica para evitar salir del directorio
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
        
    file_path = f"reportes/{filename}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return {"status": "deleted", "filename": filename}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error borrando archivo: {e}")
            
    raise HTTPException(status_code=404, detail="Reporte no encontrado")

@app.get("/api/random_images")
async def get_random_images():
    # Buscamos archivos en la carpeta static que sean imágenes y empiecen con 'img'
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif")
    
    try:
        files = [f for f in os.listdir(STATIC_DIR) 
                 if f.lower().endswith(valid_extensions) and f.startswith("img")]
        
        # Si hay 2 o más imágenes, escogemos 2 al azar sin repetir
        if len(files) >= 2:
            selected = random.sample(files, 2)
        # Si solo hay 1, la repetimos
        elif len(files) == 1:
            selected = [files[0], files[0]]
        # Si no hay imágenes, devolvemos una lista vacía
        else:
            selected = []
            
        return {"images": selected}
    except Exception as e:
        return {"images": []}
