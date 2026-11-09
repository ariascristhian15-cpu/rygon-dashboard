# 👾 THIAN-CORE // RETRO WORKSTATION & OBSIDIAN PRODUCTIVITY MATRIX

> **Centro de mando de productividad, organización personal y sincronización bidireccional con Obsidian** desarrollado para **Fedora Linux**.

Combina una estética retro / pixel-art inspirada en consolas de los 90s, tableros arcade y terminales cyberpunk con la robustez y limpieza de una suite de productividad profesional.

---

## 🚀 Inicio Rápido (Fedora Linux)

El sistema está diseñado bajo el principio de **Zero-Dependencies Out-of-the-Box** con Python 3.15, lo que significa que puedes ejecutarlo inmediatamente sin necesidad de compilar o instalar paquetes adicionales con pip:

### Opción 1: Con el script ejecutable
```bash
./run.sh
```

### Opción 2: Directo con Python 3
```bash
python3 app.py
```

Abre en tu navegador:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## 📂 Arquitectura del Proyecto

```
/home/cristhian/Documentos/thiansito/
├── app.py                      # Servidor HTTP REST (Python 3 stdlib, zero-deps)
├── run.sh                      # Script de arranque ejecutable
├── config.json                 # Configuración del servidor y ruta de la bóveda
├── requirements.txt            # Dependencias opcionales (FastAPI, Uvicorn)
├── README.md                   # Esta documentación
│
├── backend/
│   ├── __init__.py
│   ├── config.py               # Cargador y gestor de configuración
│   ├── obsidian_parser.py      # Parser de Markdown (Frontmatter, Checklists, Tablas)
│   ├── obsidian_sync.py        # Motor de sincronización bidireccional de la bóveda
│   ├── main_fastapi.py         # Variante alternativa en FastAPI con Swagger UI (/docs)
│   └── sample_data.py          # Plantillas iniciales de Markdown y frases pixel
│
├── static/
│   ├── css/
│   │   └── style.css           # Estilos retro pixel-art + terminal oscura
│   └── js/
│       ├── app.js              # Lógica de cliente, fetch API REST, estado reactivo
│       └── pixel_fx.js         # Sintetizador de audio retro (Web Audio API)
│
├── templates/
│   └── index.html              # Dashboard Web SPA responsivo
│
└── obsidian_vault/             # BÓVEDA LOCAL DE OBSIDIAN (Archivos .md reales)
    ├── .obsidian/              # Configuración de Obsidian
    ├── Dashboard_Resumen.md    # Resumen maestro
    ├── Estudios/
    │   ├── Ingenieria_Sistemas.md      # Python, PHP/MySQL, SQL, Java, Ciberseguridad
    │   ├── Diseno_Creativo.md          # Blender 3D, Ibis Paint X, Krita
    │   └── Electronica_Hardware.md     # Circuitos, Arduino, ESP32, Soldadura
    ├── Rygon_Studio/
    │   ├── Inventario.md               # Tabla de existencias, precios y stock
    │   ├── Taller_Tareas.md            # Cerámica, Crochet, Pinturas, Empaques
    │   ├── Inspiracion_Moodboard.md    # Notas e ideas estéticas
    │   └── Planificador_Redes.md       # TikTok / Instagram Reels con estados
    ├── Rutinas/
    │   ├── Habitos_Diarios.md          # Checklist diario y contador de racha
    │   └── Horario_Semanal.md          # Bloques de tiempo estructurados
    └── Notas/
        └── Bienvenida.md               # Notas rápidas creadas en Markdown
```

---

## 🔄 ¿Cómo Funciona la Sincronización con Obsidian?

1. **Lectura y Escritura Nativa en Markdown**: Cada vez que marcas una casilla de verificación o agregas un elemento desde el Dashboard Web, el backend en Python actualiza atómicamente el archivo `.md` correspondiente dentro de la carpeta `obsidian_vault/`.
2. **Edición Directa desde Obsidian**: Si abres Obsidian en Fedora y modificas cualquier lista de tareas (`- [ ]` a `- [x]`) o editas la tabla de inventario, el Dashboard Web detecta los cambios mediante su motor de auto-refresco y los refleja al instante.
3. **Cómo abrir la bóveda en la aplicación oficial de Obsidian**:
   - Abre **Obsidian**.
   - Haz clic en **"Abrir carpeta como bóveda"** (*Open folder as vault*).
   - Selecciona la carpeta: `/home/cristhian/Documentos/thiansito/obsidian_vault`.
   - ¡Listo! Podrás editar tus notas y verlas reflejadas en la web simultáneamente.

---

## 🎮 Características y Módulos

### 1. Estética Retro Pixel-Art & Terminal Oscura
- Paleta nostálgica de alto contraste: Fondo terminal oscuro (`#0e1117`), acentos naranja retro (`#ff7a29`), crema cálido (`#f7eed8`), verde fósforo CRT (`#00e676`) y azul ciberpunk (`#38bdf8`).
- Bordes definidos tipo pixel-box con sombras duras arcade.
- Filtro CRT scanlines sutil.
- Sistema de sonido 8-bits retro integrado mediante Web Audio API (con botón para silenciar).
- Barra de Gamificación XP: Gana +25 XP por cada tarea completada y +50 XP por hábitos diarios cumplidos para subir de nivel.

### 2. Módulo de Estudios y Cursos
- **Ingeniería de Sistemas**: Python (APIs, OOP), PHP & MySQL, SQL relacional avanzado, Java & Spring Boot, Ciberseguridad & Redes (OWASP, Linux Hardening).
- **Diseño Creativo**: Blender 3D (Hard-surface, Shading), Ibis Paint X, Krita.
- **Electrónica y Hardware Básico**: Multímetro, Circuitos, Arduino, ESP32 IoT, Soldadura.
- Barra de progreso porcentual dinámica por ruta.
- Filtro rápido para ocultar tareas completadas y mostrar solo pendientes.

### 3. Módulo Emprendimiento "Rygon Studio"
- **Taller de Manufactura**: Checklist dividido en Cerámica, Crochet, Pinturas & Dibujos y Empaques / Packaging.
- **Inventario y Stock**: Tabla completa con ID, Stock, Precio de Venta, Costo Material y Estado de reposición.
- **Planificador de Redes Sociales**: Calendario para TikTok e Instagram Reels con selector de estado dinámico (`💡 Idea`, `📝 Guion`, `🎬 Grabando`, `✂️ Editado`, `🚀 Publicado`).
- **Banco de Inspiración & Moodboard**: Editor Markdown en vivo para anotar enlaces de Pinterest, paletas y conceptos artísticos.

### 4. Módulo de Hábitos y Horario Diario
- **Tracker de Hábitos**: Casillas de verificación con cálculo de racha en días y registro de mejor récord.
- **Consola Interactiva Pixel-Art**: Generador interactivo de frases inspiradoras para desarrolladores y artistas.
- **Horario Semanal**: Matriz de bloques de tiempo (Lunes-Miércoles, Jueves-Viernes, Sábados-Domingos).

### 5. Explorador de Bóveda y Notas Rápidas
- Crea nuevas notas `.md` desde el modal web y se guardarán de inmediato en `obsidian_vault/Notas/`.
- Visualizador y visor rápido integrado.

---

## ⚙️ Configuración Personalizada

Puedes cambiar el puerto o apuntar a otra bóveda de Obsidian editando `config.json` o usando la variable de entorno:

```bash
export OBSIDIAN_VAULT_PATH="/ruta/a/mi/otra/boveda"
python3 app.py
```

O desde la pestaña **⚙️ CONFIGURACIÓN** en el dashboard web.

---

## ⚡ Variante FastAPI (Opcional)

Si deseas utilizar FastAPI con documentación interactiva Swagger (`/docs`):

```bash
# 1. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar con uvicorn
uvicorn backend.main_fastapi:app --host 0.0.0.0 --port 8080 --reload
```
Accede a la documentación automática de la API en: **http://localhost:8080/docs**
