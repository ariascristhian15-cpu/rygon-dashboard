"""
Plantillas y datos iniciales para la Bóveda de Obsidian y el Dashboard.
Todos los archivos se generan en formato Markdown 100% nativo de Obsidian.
"""

INITIAL_VAULT_FILES = {
    # --- ESTUDIOS Y CURSOS ---
    "Estudios/Ingenieria_Sistemas.md": """---
title: "Ingeniería de Sistemas - Rutas de Aprendizaje"
category: "Estudios"
icon: "terminal"
progress_overall: 65
updated: "2026-11-08"
tags: [ingenieria, programacion, backend, ciberseguridad]
---

# 💻 Ingeniería de Sistemas & Desarrollo

Rutas de aprendizaje técnico, arquitectura y seguridad informática.

## 🐍 1. Python & Backend Moderno
- [x] Fundamentos de Python y estructuras de datos nativas #python
- [x] Paradigma de Orientación a Objetos (POO) y diseño modular #python
- [x] Desarrollo de APIs REST con Flask y FastAPI #python
- [ ] Automatización de scripts de Linux y parsing de Markdown #python (80%)
- [ ] Concurrencia con asyncio y multiprocessing #python (0%)

## 🐘 2. PHP & MySQL
- [x] Sintaxis moderna de PHP y manejo de sesiones #php
- [x] Conexión PDO segura y prevención de inyecciones SQL #php #mysql
- [ ] Desarrollo de arquitectura MVC sin frameworks #php (60%)
- [ ] Normalización de bases de datos relacionales en MySQL #mysql (50%)
- [ ] Consultas avanzadas: JOINs, Subconsultas e Índices #mysql (40%)

## ☕ 3. Java & Arquitectura Empresarial
- [x] Fundamentos de tipos, colecciones y genéricos en Java #java
- [ ] Principios SOLID y Patrones de Diseño GoF en Java #java (40%)
- [ ] Introducción a Spring Boot y Spring Data JPA #java (20%)
- [ ] Creación de microservicios con persistencia en PostgreSQL #java (0%)

## 🛡️ 4. Ciberseguridad & Redes
- [x] Modelo OSI y protocolo TCP/IP a fondo #redes #seguridad
- [x] Fundamentos de Linux para administración de servidores (Fedora/Debian) #linux
- [ ] Escaneo de vulnerabilidades y puertos con Nmap y Wireshark #ciberseguridad (50%)
- [ ] OWASP Top 10: Detección y mitigación en aplicaciones web #ciberseguridad (30%)
- [ ] Hardening de sistemas operativos y firewall (iptables/nftables) #ciberseguridad (15%)
""",

    "Estudios/Diseno_Creativo.md": """---
title: "Rutas de Diseño y Creación Digital"
category: "Estudios"
icon: "palette"
progress_overall: 52
updated: "2026-11-08"
tags: [arte, diseno, 3d, ilustracion]
---

# 🎨 Rutas de Aprendizaje en Diseño

Técnicas digitales para producción gráfica y assets visuales.

## 🍩 1. Blender 3D
- [x] Navegación en el viewport, atajos de teclado y transformaciones básicas #blender
- [x] Modelado de objetos Hard-Surface y uso de modificadores (Bevel, Subdivision) #blender
- [ ] Escultura digital de personajes orgánicos y retopología #blender (35%)
- [ ] Creación de materiales con Shading Nodes e iluminación en Cycles/Eevee #blender (45%)
- [ ] Renderizado y animación básica para videos cortos de Rygon Studio #blender (20%)

## 📱 2. Ibis Paint X
- [x] Configuración de lienzos, resoluciones DPI y gestión de capas #ibispaint
- [x] Bocetado rápido y técnicas de entintado fluido (Lineart) #ibispaint
- [ ] Uso de máscaras de recorte, modos de fusión y tramas retro #ibispaint (50%)
- [ ] Creación de stickers y diseños para merchandising #ibispaint (60%)

## 🖌️ 3. Krita
- [x] Calibración de sensibilidad de presión y pinceles recomendados #krita
- [x] Teoría del color aplicada a la ilustración digital #krita
- [ ] Pintura digital con textura tradicional y luces volumétricas #krita (40%)
- [ ] Creación de sprites y fondos estilo Pixel-Art / Matte Painting #krita (30%)
""",

    "Estudios/Electronica_Hardware.md": """---
title: "Electrónica y Hardware Básico"
category: "Estudios"
icon: "cpu"
progress_overall: 40
updated: "2026-11-08"
tags: [hardware, electronica, arduino, iot]
---

# ⚡ Electrónica y Hardware

Conceptos fundamentales de circuitos, microcontroladores y prototipado físico.

## 🔌 1. Fundamentos de Circuitos
- [x] Ley de Ohm, potencia y cálculo de resistencias #electronica
- [x] Uso correcto del multímetro digital (Voltaje, Corriente, Continuidad) #taller
- [ ] Transistores BJT y MOSFET como interruptores y amplificadores #electronica (30%)
- [ ] Diseño y ruteo de PCBs sencillas con KiCad #hardware (10%)

## 🤖 2. Microcontroladores & IoT
- [x] Programación de entradas/salidas digitales en Arduino UNO #arduino
- [ ] Lectura de sensores analógicos (LDR, termistores, potenciómetros) #arduino (60%)
- [ ] Comunicación serie, I2C y SPI con pantallas OLED/LCD #arduino (40%)
- [ ] Proyectos conectados con ESP32 (WiFi, MQTT y dashboards web) #esp32 (20%)

## 🛠️ 3. Taller y Soldadura
- [x] Reglas de seguridad en el banco de trabajo y extracción de humos #taller
- [x] Técnicas de soldadura estaño-plomo y limpieza de puntas #soldadura
- [ ] Desoldadura con malla y bomba de succión #soldadura (50%)
""",

    # --- RYGON STUDIO (EMPRENDIMIENTO) ---
    "Rygon_Studio/Inventario.md": """---
title: "Inventario de Productos - Rygon Studio"
category: "Rygon_Studio"
icon: "box"
updated: "2026-11-08"
tags: [rygon, inventario, ventas, artesania]
---

# 📦 Inventario Central - Rygon Studio

Control de existencias, precios y materias primas.

| ID | Producto | Categoría | Stock | Precio_Venta | Costo_Material | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| P-001 | Taza Cerámica Pixel Cat | Cerámica | 8 | $35.000 | $12.000 | Disponible |
| P-002 | Amigurumi Fantasmita Retro | Crochet | 5 | $28.000 | $8.000 | Bajo Stock |
| P-003 | Maceta Esculpida Duende | Cerámica | 3 | $42.000 | $15.000 | Bajo Stock |
| P-004 | Lámina Print A5 Cyberpunk | Dibujo | 18 | $15.000 | $3.500 | Disponible |
| P-005 | Posavasos Tejido Pixel Heart | Crochet | 12 | $12.000 | $3.000 | Disponible |
| P-006 | Pack Stickers Holográficos x5 | Merch | 25 | $10.000 | $2.200 | Disponible |
| P-007 | Cuadro Mini Óleo Galaxia | Pintura | 2 | $55.000 | $18.000 | Casi Agotado |
""",

    "Rygon_Studio/Taller_Tareas.md": """---
title: "Tareas de Producción de Taller - Rygon Studio"
category: "Rygon_Studio"
icon: "hammer"
updated: "2026-11-08"
tags: [rygon, taller, produccion]
---

# 🔨 Tareas de Taller y Producción

Checklist de manufactura artesanal por disciplina.

## 🏺 Cerámica
- [x] Amasar arcilla y desgasificar para lote de tazas #ceramica
- [x] Tornear y retorner 6 bases de macetas #ceramica
- [ ] Aplicar esmaltes bajo cubierta (diseños retro) #ceramica (40%)
- [ ] Cargar horno para primera quema de bizcocho #ceramica (0%)

## 🧶 Crochet
- [x] Comprar hilo de algodón mercerizado verde y naranja #crochet
- [x] Tejer 4 cabezas para amigurumis coleccionables #crochet
- [ ] Rellenar y coser extremidades con remate invisible #crochet (50%)
- [ ] Colocar ojos de seguridad con arandelas fijas #crochet (0%)

## 🎨 Pinturas & Dibujos
- [x] Preparar imprimación de 3 lienzos de madera con gesso #pintura
- [ ] Boceto base con carboncillo para serie botánica retro #dibujo (80%)
- [ ] Aplicar barniz satinado protector a láminas terminadas #pintura (0%)

## 📦 Empaques & Packaging
- [x] Estampar logotipo Rygon Studio en 30 bolsas de papel kraft #packaging
- [x] Diseñar tarjetas de agradecimiento estilo ticket arcade #packaging
- [ ] Armar 10 cajas reforzadas con viruta de papel protectora #packaging (60%)
- [ ] Imprimir etiquetas de envío con código de seguimiento #packaging (0%)
""",

    "Rygon_Studio/Inspiracion_Moodboard.md": """---
title: "Banco de Inspiración & Moodboard"
category: "Rygon_Studio"
icon: "sparkles"
updated: "2026-11-08"
tags: [moodboard, creatividad, estetica]
---

# ✨ Moodboard & Banco de Ideas

Referencias visuales, paletas y conceptos para nuevas colecciones.

## 🎯 Concepto Visual: Nostalgia Arcade & Cozy Craft
- Mezcla de formas orgánicas cálidas (cerámica rústica, lana suave) con iconografía retro de videojuegos de 8 bits y 16 bits.
- Colores clave: Naranja quemado (#E65100), Crema avainillado (#FFF8E7), Verde terminal CRT (#00E676), Violeta cian oscuro (#1A1B26).

## 🔗 Enlaces y Referencias
- [Pinterest: Cerámica geométrica y esmaltes mates](https://pinterest.com) - Ideas para texturas con bajorrelieve.
- [Instagram: Creadores de Amigurumi japoneses](https://instagram.com) - Patrones limpios y proporciones chibi.
- [Behance: Branding para talleres artesanales](https://behance.net) - Empaques sostenibles con tipografías pixel.

## 💡 Banco de Ideas de Productos
- Macetas con forma de consola retro Game Boy donde las plantas simulan el cartucho.
- Sets de posavasos con sprites de pociones mágicas (Salud, Maná, Energía).
- Pins cerámicos esmaltados con íconos de diskettes y comandos de terminal.
""",

    "Rygon_Studio/Planificador_Redes.md": """---
title: "Planificador de Redes Sociales - Rygon Studio"
category: "Rygon_Studio"
icon: "video"
updated: "2026-11-08"
tags: [redes, reels, tiktok, marketing]
---

# 📱 Planificador Semanal de Contenido (TikTok & Reels)

Cronograma de grabaciones, hooks y estados de publicación.

| ID | Red_Social | Titulo_Contenido | Enfoque_Hook | Fecha_Programada | Estado |
| --- | --- | --- | --- | --- | --- |
| RED-01 | TikTok | "Cómo esmaltar una taza en 30 segundos" | ASMR de sonido de espátula y esmalte | 2026-11-10 | 🚀 Publicado |
| RED-02 | Reels IG | "Modelando una maceta retro paso a paso" | Timelapse rápido con música lofi | 2026-11-11 | ✂️ Editado |
| RED-03 | TikTok | "Empacando un pedido para cliente gamer" | Empaque con caja personalizada y sticker | 2026-11-12 | 🎬 Grabando |
| RED-04 | Reels IG | "Tejiendo un mini fantasma en crochet" | Tutorial express con patrón en pantalla | 2026-11-14 | 📝 Guion |
| RED-05 | TikTok | "Día en la vida de un estudiante y artesano" | V-Log dinámico Fedora + Taller | 2026-11-16 | 💡 Idea |
""",

    # --- RUTINAS Y HÁBITOS ---
    "Rutinas/Habitos_Diarios.md": """---
title: "Tracker de Hábitos Diarios"
category: "Rutinas"
icon: "check-circle"
current_streak_days: 7
best_streak_days: 21
updated: "2026-11-08"
tags: [habitos, disciplina, progreso]
---

# ⚡ Tracker de Hábitos & Rendimiento Diario

Cada hábito cumplido otorga +50 XP al sistema personal.

## 📅 Hábitos Diarios Clave
- [x] Beber 2L de agua durante la jornada #salud
- [x] Bloque de Programación / Ingeniería (mínimo 1h) #sistemas
- [ ] Práctica de Diseño o Producción en Taller Rygon (45m) #rygon
- [x] Ejercicio físico / Caminata al aire libre (30m) #salud
- [ ] Estudio técnico de Ciberseguridad o Redes #estudio
- [x] Revisión y sincronización de notas en Obsidian #organizacion
- [ ] Desconexión de pantallas 30 min antes de dormir #descanso
""",

    "Rutinas/Horario_Semanal.md": """---
title: "Horario y Bloques de Productividad"
category: "Rutinas"
icon: "clock"
updated: "2026-11-08"
tags: [horario, bloques, agenda]
---

# ⏰ Horario Semanal Estructurado

Organización por bloques de tiempo para balancear ingeniería y arte.

| Franja_Horaria | Lunes_Miercoles | Jueves_Viernes | Sabado_Domingo |
| --- | --- | --- | --- |
| 07:00 - 08:30 | Rutina matutina, café y lectura técnica | Rutina matutina y planificación | Despertar suave y desayuno nutritivo |
| 08:30 - 12:30 | Ingeniería de Sistemas (Python/Java/SQL) | Ingeniería (Ciberseguridad/Linux) | Taller Libre Rygon (Cerámica/Pintura) |
| 12:30 - 14:00 | Almuerzo y descanso sin pantallas | Almuerzo y caminata | Almuerzo familiar o amigos |
| 14:00 - 17:30 | Taller Rygon (Producción y Pedidos) | Diseño Digital (Blender/Krita) | Grabación de Reels y TikToks |
| 17:30 - 19:00 | Deporte, ejercicio y ducha | Deporte y aire libre | Planificación de la próxima semana |
| 19:00 - 21:00 | Proyectos personales / Código libre | Proyectos IoT / Electrónica | Ocio, videojuegos retro y descanso |
""",

    "Dashboard_Resumen.md": """---
title: "Dashboard Central de Control"
type: "dashboard"
system: "Fedora Workstation"
updated: "2026-11-08"
status: "OPERATIVO"
---

# 🎛️ Terminal Central de Productividad

Bienvenido a tu estación central de control.

- **Bóveda**: Sincronizada y activa.
- **Enfoque actual**: Sistemas Backend + Taller Rygon Studio.
- **Consejo del día**: *La consistencia vence al talento cuando el talento no es consistente.*
""",

    "Notas/Bienvenida.md": """---
title: "Nota de Inicio - Sistema Sincronizado"
category: "Notas"
created: "2026-11-08"
tags: [bienvenida, obsidian, thiancore]
---

# 🚀 Bienvenido a tu Centro de Mando

Este sistema conecta tu interfaz web con tus archivos locales Markdown de Obsidian.
Cualquier cambio que realices aquí o en tu editor Obsidian se refleja inmediatamente.

### Atajos útiles:
- Abre esta carpeta (`obsidian_vault`) desde **Obsidian -> Open folder as vault**.
- En la interfaz web puedes alternar el filtro de pendientes, agregar nuevos productos y marcar tareas al instante.
"""
}

MOTIVATIONAL_QUOTES = [
    {"quote": "Cada línea de código y cada pieza de arcilla moldean tu futuro.", "author": "THIAN-CORE", "tag": "CREACIÓN"},
    {"quote": "No busques la perfección en un día; busca el avance constante en cada byte.", "author": "TERMINAL ARCHITECT", "tag": "DISCIPLINA"},
    {"quote": "La creatividad es la inteligencia divirtiéndose con cables, pinceles y algoritmos.", "author": "RYGON STUDIO", "tag": "ARTE"},
    {"quote": "Domina los fundamentos: en programación y en la vida, las bases lo sostienen todo.", "author": "LINUX PHILOSOPHY", "tag": "INGENIERÍA"},
    {"quote": "Un bug no es un error, es un desafío esperando ser resuelto con paciencia.", "author": "DEBUGGER MIND", "tag": "HACKER"},
    {"quote": "El arte manual da alma a la mente técnica. El equilibrio es tu mayor superpoder.", "author": "WORKBENCH MASTER", "tag": "BALANCE"},
    {"quote": "Compila tus ideas, ejecuta tus proyectos y no temas a las excepciones.", "author": "SYSTEM KERNEL", "tag": "FOCO"}
]
