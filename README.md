# gamingeducation4all
build yourself an amazing plattform for education with gaming style

🏗️ Construyendo a mis Ingenieras
Una plataforma educativa interactiva diseñada para gestionar retos de ingeniería, capturar evidencias de aprendizaje y visualizar el progreso de las estudiantes en tiempo real. Este proyecto utiliza un backend moderno con FastAPI y una interfaz dinámica con Tailwind CSS.

🌟 Características
Gestión de Retos: Sistema dinámico para subir nuevos desafíos mediante código HTML directamente desde la interfaz de administrador, incluso con la ayuda de un GPT o GEMA preconfigurado. (Ver detalles para crearlo abajo)

Recolección de Evidencias: Estructura rígida de 3 pasos (paso, respuesta y razonamiento) para asegurar un proceso de aprendizaje lógico.

Panel de Administración: Acceso protegido por clave para visualizar todos los reportes enviados y gestionar (crear/borrar) los retos.

Historial Académico: Buscador para que las estudiantes consulten sus participaciones anteriores por nombre.

Persistencia Local: Almacenamiento eficiente mediante archivos JSON y estructura de carpetas organizada.

🛠️ Tecnologías Utilizadas
Backend: (Python 3.10+)

Frontend: HTML5, JavaScript (ES6+),

Modelado de Datos:

Servidor: Uvicorn

📂 Estructura del Proyecto
🚀 Instalación y Uso
1. Clonar el repositorio
2. Instalar dependencias
Asegúrate de tener Python instalado. Luego instala FastAPI y Uvicorn:

3. Ejecutar la aplicación
La aplicación estará disponible en http://127.0.0.1:8000.

🔐 Secciones del Sistema
[!IMPORTANT] Nota para el desarrollador: La clave por defecto es admin. Se recomienda cambiarla en las funciones checkAdmin del frontend y en los endpoints del backend para entornos de producción.

🤝 Contribución
Si deseas añadir nuevos tipos de validaciones o mejorar la interfaz:

Haz un Fork del proyecto.

Crea una rama (git checkout -b feature/mejora).

Haz commit de tus cambios.

Envía un Pull Request.

Desarrollado con fines educativos para fomentar el talento en ingeniería. 🚀
