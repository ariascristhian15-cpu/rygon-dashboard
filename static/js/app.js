/**
 * ====================================================================
 * THIAN-CORE // FULL-STACK CLIENT APPLICATION LOGIC
 * Sincronización continua con Bóveda de Obsidian y Gestión de Módulos
 * ====================================================================
 */

const AppState = {
  stats: null,
  studies: {},
  inventory: [],
  workshop: [],
  social: [],
  habits: { streak_days: 0, habits: [] },
  schedule: [],
  notes: [],
  weeklyCurrent: null,
  weeklyHistory: [],
  weeklyAggregates: null,
  weeklySupabase: null,
  weeklySummaryOpen: false,
  weeklyAckedIds: new Set(),
  currentTab: "estudios",
  currentRygonSubtab: "taller",
  filterOnlyPending: false
};

// ====================================================================
// TOAST NOTIFICATIONS (TERMINAL LOGS)
// ====================================================================
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast-msg";
  if (type === "error") {
    toast.style.borderColor = "var(--retro-red)";
  } else if (type === "info") {
    toast.style.borderColor = "var(--retro-blue)";
  }

  const icon = type === "error" ? "❌" : (type === "info" ? "ℹ️" : "💾");
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ====================================================================
// API FETCH HELPERS
// ====================================================================
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`Error en GET ${endpoint}:`, err);
    return null;
  }
}

async function apiPost(endpoint, data = {}) {
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`Error en POST ${endpoint}:`, err);
    showToast(`Error de conexión con el backend: ${err.message}`, "error");
    return null;
  }
}

async function apiDelete(endpoint) {
  try {
    const res = await fetch(endpoint, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`Error en DELETE ${endpoint}:`, err);
    showToast(`Error eliminando registro: ${err.message}`, "error");
    return null;
  }
}

// ====================================================================
// CARGA Y SINCRONIZACIÓN GENERAL
// ====================================================================
async function refreshAllData(showNotification = false) {
  const [stats, quote] = await Promise.all([
    apiGet("/api/stats"),
    apiGet("/api/quote")
  ]);

  if (stats) {
    AppState.stats = stats;
    renderStats(stats);
    renderXPBar(stats);
    updateVaultBadge(stats.vault_path);
  }

  if (quote && !document.getElementById("quote-display").innerText.trim()) {
    renderQuote(quote);
  }

  // Cargar según la pestaña activa o precargar todo
  await Promise.all([
    loadStudies(),
    loadRygonData(),
    loadHabitsAndSchedule(),
    loadWeeklyData(),
    loadNotes()
  ]);

  if (showNotification) {
    window.pixelFX.playSuccessSound();
    showToast("[SYNC: OBSIDIAN] Bóveda sincronizada correctamente.");
  }
}

function updateVaultBadge(path) {
  const badge = document.getElementById("vault-badge-text");
  if (badge && path) {
    const parts = path.split("/");
    const shortName = parts.slice(-2).join("/");
    badge.innerText = `Obsidian: ${shortName}`;
    badge.title = path;
  }
}

function renderStats(stats) {
  document.getElementById("stat-total").innerText = stats.total_tasks || 0;
  document.getElementById("stat-completed").innerText = stats.completed_tasks || 0;
  document.getElementById("stat-pending").innerText = stats.pending_tasks || 0;
  document.getElementById("stat-streak").innerText = `${stats.habits_streak || 0} DÍAS`;
  document.getElementById("stat-inventory").innerText = stats.inventory_products_count || 0;
}

function renderXPBar(stats) {
  // La barra superior muestra la XP del CICLO SEMANAL (se reinicia cada
  // domingo), mientras el nivel se calcula con la XP histórica acumulada.
  const weekly = stats.weekly || {};
  const metrics = weekly.metrics || {};
  const xpPerLevel = weekly.xp_per_level || 500;
  const weeklyXP = Number(
    metrics.xp_earned !== undefined
      ? metrics.xp_earned
      : (stats.completed_tasks * 25) + (stats.habits_completed * 50)
  );
  const lifetimeXP = Number(
    stats.lifetime_xp !== undefined ? stats.lifetime_xp : weeklyXP
  );
  const currentLevel = stats.lifetime_level || weekly.lifetime_level ||
    (Math.floor(lifetimeXP / xpPerLevel) + 1);
  const progressPercent = Math.min(
    100,
    Math.round((weeklyXP / xpPerLevel) * 100)
  );

  document.getElementById("xp-level-display").innerText =
    `LVL ${currentLevel} // HACKER-ARTISAN · CICLO SEMANAL`;
  document.getElementById("xp-fill").style.width = `${progressPercent}%`;
  document.getElementById("xp-numbers").innerText =
    `${weeklyXP} / ${xpPerLevel} XP SEMANA (${progressPercent}%) · TOTAL ${lifetimeXP} XP`;
}

function renderQuote(q) {
  if (!q) return;
  document.getElementById("quote-display").innerText = `"${q.quote}"`;
  document.getElementById("quote-author").innerText = `— ${q.author} [${q.tag}]`;
}

async function fetchNextQuote() {
  window.pixelFX.playKeyClick();
  const q = await apiGet("/api/quote");
  if (q) renderQuote(q);
}

// ====================================================================
// MÓDULO 1: ESTUDIOS Y CURSOS
// ====================================================================
async function loadStudies() {
  const data = await apiGet("/api/studies");
  if (!data) return;
  AppState.studies = data;
  renderStudies(data);
}

function renderStudies(studies) {
  const container = document.getElementById("studies-container");
  if (!container) return;

  container.innerHTML = "";

  Object.values(studies).forEach(track => {
    const card = document.createElement("div");
    card.className = "study-track-card";

    let sectionsHtml = "";
    track.sections.forEach(sec => {
      let tasksHtml = "";
      sec.tasks.forEach(task => {
        if (AppState.filterOnlyPending && task.completed) return;

        const checkedAttr = task.completed ? "checked" : "";
        const completedClass = task.completed ? "completed" : "";
        const tagsHtml = (task.tags || []).map(t => `<span class="tag-badge">#${t}</span>`).join(" ");

        tasksHtml += `
          <div class="task-item ${completedClass}">
            <input type="checkbox" class="pixel-checkbox" ${checkedAttr} 
                   onchange="handleToggleStudyTask('${track.file_key}', '${encodeURIComponent(task.raw)}', this.checked)">
            <div class="task-content">
              <span>${task.text}</span>
              ${tagsHtml}
            </div>
          </div>
        `;
      });

      if (tasksHtml) {
        sectionsHtml += `
          <div class="section-group">
            <div class="section-title">${sec.title}</div>
            <div class="tasks-list">${tasksHtml}</div>
          </div>
        `;
      }
    });

    card.innerHTML = `
      <div class="track-header">
        <h3>${track.title}</h3>
        <div class="track-progress-badge">${track.progress}%</div>
      </div>
      <div class="track-body">
        ${sectionsHtml || '<div style="color: #666; font-size:12px;">No hay tareas pendientes en esta ruta.</div>'}
      </div>
    `;

    container.appendChild(card);
  });
}

async function handleToggleStudyTask(fileKey, encodedRawText, completed) {
  const taskText = decodeURIComponent(encodedRawText);
  if (completed) {
    window.pixelFX.playSuccessSound();
  } else {
    window.pixelFX.playBlip();
  }

  const res = await apiPost("/api/studies/toggle", {
    file_key: fileKey,
    task_text: taskText,
    completed: completed
  });

  if (res && res.success) {
    showToast(`[OBSIDIAN] Actualizado en Estudios/${fileKey}.md`);
    refreshAllData(false);
  }
}

function openAddStudyModal() {
  window.pixelFX.playKeyClick();
  document.getElementById("modal-add-study").classList.add("active");
}

async function submitAddStudy(e) {
  e.preventDefault();
  const fileKey = document.getElementById("study-modal-track").value;
  const section = document.getElementById("study-modal-section").value;
  const text = document.getElementById("study-modal-text").value;
  const tags = document.getElementById("study-modal-tags").value;

  if (!text) return;

  const res = await apiPost("/api/studies/add", {
    file_key: fileKey,
    section: section,
    text: text,
    tags: tags
  });

  if (res && res.success) {
    closeModal("modal-add-study");
    document.getElementById("form-add-study").reset();
    window.pixelFX.playSuccessSound();
    showToast("[OBSIDIAN] Nueva tarea agregada a la bóveda");
    refreshAllData(false);
  }
}

// ====================================================================
// MÓDULO 2: RYGON STUDIO (TALLER, INVENTARIO, MOODBOARD, REDES)
// ====================================================================
async function loadRygonData() {
  const [inv, ws, mb, soc] = await Promise.all([
    apiGet("/api/rygon/inventory"),
    apiGet("/api/rygon/workshop"),
    apiGet("/api/rygon/moodboard"),
    apiGet("/api/rygon/social")
  ]);

  if (inv) { AppState.inventory = inv; renderInventory(inv); }
  if (ws) { AppState.workshop = ws; renderWorkshop(ws); }
  if (mb) { renderMoodboard(mb); }
  if (soc) { AppState.social = soc; renderSocialPlanner(soc); }
}

function renderInventory(items) {
  const tbody = document.getElementById("inventory-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  items.forEach(item => {
    const tr = document.createElement("tr");
    const statusClass = (item.Estado || "").toLowerCase().replace(/\s+/g, "-");
    tr.innerHTML = `
      <td><strong>${item.ID || ""}</strong></td>
      <td>${item.Producto || ""}</td>
      <td><span class="tag-badge">${item.Categoría || ""}</span></td>
      <td><strong style="color:var(--retro-cream);">${item.Stock || 0}</strong></td>
      <td style="color:var(--retro-green); font-family:var(--font-terminal); font-size:18px;">${item.Precio_Venta || ""}</td>
      <td style="color:var(--retro-cream-muted);">${item.Costo_Material || ""}</td>
      <td><span class="status-badge ${statusClass}">${item.Estado || ""}</span></td>
      <td>
        <button class="pixel-btn btn-sm" style="border-color:var(--retro-red);" onclick="deleteInventoryItem('${item.ID}')">X</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function deleteInventoryItem(id) {
  if (!confirm(`¿Eliminar producto ${id} del inventario?`)) return;
  window.pixelFX.playKeyClick();
  const res = await apiDelete(`/api/rygon/inventory?id=${encodeURIComponent(id)}`);
  if (res && res.success) {
    showToast(`[OBSIDIAN] Producto ${id} eliminado de Inventario.md`);
    loadRygonData();
    refreshAllData(false);
  }
}

function openAddInventoryModal() {
  window.pixelFX.playKeyClick();
  document.getElementById("modal-add-inventory").classList.add("active");
}

async function submitAddInventory(e) {
  e.preventDefault();
  const item = {
    ID: document.getElementById("inv-modal-id").value || `P-${Date.now().toString().slice(-3)}`,
    Producto: document.getElementById("inv-modal-name").value,
    Categoría: document.getElementById("inv-modal-cat").value,
    Stock: document.getElementById("inv-modal-stock").value,
    Precio_Venta: document.getElementById("inv-modal-price").value,
    Costo_Material: document.getElementById("inv-modal-cost").value,
    Estado: document.getElementById("inv-modal-status").value
  };

  const res = await apiPost("/api/rygon/inventory", { item });
  if (res && res.success) {
    closeModal("modal-add-inventory");
    document.getElementById("form-add-inventory").reset();
    window.pixelFX.playSuccessSound();
    showToast("[OBSIDIAN] Producto guardado en Inventario.md");
    loadRygonData();
    refreshAllData(false);
  }
}

function renderWorkshop(categories) {
  const container = document.getElementById("workshop-container");
  if (!container) return;
  container.innerHTML = "";

  categories.forEach(cat => {
    const card = document.createElement("div");
    card.className = "study-track-card";

    let tasksHtml = "";
    cat.tasks.forEach(t => {
      if (AppState.filterOnlyPending && t.completed) return;
      const checked = t.completed ? "checked" : "";
      const compClass = t.completed ? "completed" : "";
      tasksHtml += `
        <div class="task-item ${compClass}">
          <input type="checkbox" class="pixel-checkbox" ${checked}
                 onchange="handleToggleWorkshop('${encodeURIComponent(t.raw)}', this.checked)">
          <div class="task-content">
            <span>${t.text}</span>
            ${(t.tags || []).map(tg => `<span class="tag-badge">#${tg}</span>`).join(" ")}
          </div>
        </div>
      `;
    });

    card.innerHTML = `
      <div class="track-header">
        <h3>${cat.category}</h3>
        <span class="tag-badge">TALLER</span>
      </div>
      <div class="track-body">
        ${tasksHtml || '<div style="color:#666; font-size:12px;">Sin tareas pendientes.</div>'}
      </div>
    `;
    container.appendChild(card);
  });
}

async function handleToggleWorkshop(encodedRawText, completed) {
  const rawText = decodeURIComponent(encodedRawText);
  if (completed) window.pixelFX.playSuccessSound();
  else window.pixelFX.playBlip();

  const res = await apiPost("/api/rygon/workshop/toggle", {
    task_text: rawText,
    completed: completed
  });
  if (res && res.success) {
    showToast("[OBSIDIAN] Actualizado en Taller_Tareas.md");
    refreshAllData(false);
  }
}

function openAddWorkshopModal() {
  window.pixelFX.playKeyClick();
  document.getElementById("modal-add-workshop").classList.add("active");
}

async function submitAddWorkshop(e) {
  e.preventDefault();
  const category = document.getElementById("ws-modal-cat").value;
  const text = document.getElementById("ws-modal-text").value;
  const tag = document.getElementById("ws-modal-tag").value;

  const res = await apiPost("/api/rygon/workshop/add", { category, text, tag });
  if (res && res.success) {
    closeModal("modal-add-workshop");
    document.getElementById("form-add-workshop").reset();
    window.pixelFX.playSuccessSound();
    showToast("[OBSIDIAN] Tarea de taller añadida");
    loadRygonData();
    refreshAllData(false);
  }
}

function renderMoodboard(mb) {
  const editor = document.getElementById("moodboard-text");
  if (editor) {
    editor.value = mb.raw_markdown || "";
  }
}

async function saveMoodboardContent() {
  window.pixelFX.playKeyClick();
  const raw = document.getElementById("moodboard-text").value;
  const res = await apiPost("/api/rygon/moodboard", { raw_markdown: raw });
  if (res && res.success) {
    window.pixelFX.playSuccessSound();
    showToast("[OBSIDIAN] Moodboard guardado con éxito.");
  }
}

function renderSocialPlanner(posts) {
  const tbody = document.getElementById("social-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  posts.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${p.ID || ""}</strong></td>
      <td><span class="tag-badge" style="border-color:var(--retro-orange); color:var(--retro-orange);">${p.Red_Social || ""}</span></td>
      <td><strong>${p.Titulo_Contenido || ""}</strong></td>
      <td style="color:var(--retro-cream-muted); font-size:12px;">${p.Enfoque_Hook || ""}</td>
      <td><code>${p.Fecha_Programada || ""}</code></td>
      <td>
        <select class="form-select" style="padding:2px 6px; font-size:11px;" 
                onchange="updateSocialPostStatus('${p.ID}', this.value)">
          <option value="💡 Idea" ${p.Estado && p.Estado.includes("Idea") ? "selected" : ""}>💡 Idea</option>
          <option value="📝 Guion" ${p.Estado && p.Estado.includes("Guion") ? "selected" : ""}>📝 Guion</option>
          <option value="🎬 Grabando" ${p.Estado && p.Estado.includes("Grabando") ? "selected" : ""}>🎬 Grabando</option>
          <option value="✂️ Editado" ${p.Estado && p.Estado.includes("Editado") ? "selected" : ""}>✂️ Editado</option>
          <option value="🚀 Publicado" ${p.Estado && p.Estado.includes("Publicado") ? "selected" : ""}>🚀 Publicado</option>
        </select>
      </td>
      <td>
        <button class="pixel-btn btn-sm" style="border-color:var(--retro-red);" onclick="deleteSocialPost('${p.ID}')">X</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function updateSocialPostStatus(id, newStatus) {
  window.pixelFX.playKeyClick();
  const post = AppState.social.find(p => p.ID === id);
  if (!post) return;
  post.Estado = newStatus;

  const res = await apiPost("/api/rygon/social", { post });
  if (res && res.success) {
    showToast(`[OBSIDIAN] Redes: ${id} cambiado a ${newStatus}`);
    refreshAllData(false);
  }
}

async function deleteSocialPost(id) {
  if (!confirm(`¿Eliminar publicación ${id}?`)) return;
  window.pixelFX.playKeyClick();
  const res = await apiDelete(`/api/rygon/social?id=${encodeURIComponent(id)}`);
  if (res && res.success) {
    showToast(`[OBSIDIAN] Publicación ${id} eliminada`);
    loadRygonData();
    refreshAllData(false);
  }
}

function openAddSocialModal() {
  window.pixelFX.playKeyClick();
  document.getElementById("modal-add-social").classList.add("active");
}

async function submitAddSocial(e) {
  e.preventDefault();
  const post = {
    ID: `RED-${(AppState.social.length + 1).toString().padStart(2, "0")}`,
    Red_Social: document.getElementById("soc-modal-platform").value,
    Titulo_Contenido: document.getElementById("soc-modal-title").value,
    Enfoque_Hook: document.getElementById("soc-modal-hook").value,
    Fecha_Programada: document.getElementById("soc-modal-date").value,
    Estado: document.getElementById("soc-modal-status").value
  };

  const res = await apiPost("/api/rygon/social", { post });
  if (res && res.success) {
    closeModal("modal-add-social");
    document.getElementById("form-add-social").reset();
    window.pixelFX.playSuccessSound();
    showToast("[OBSIDIAN] Contenido agendado en Planificador_Redes.md");
    loadRygonData();
    refreshAllData(false);
  }
}

// ====================================================================
// MÓDULO 3: HÁBITOS Y HORARIO SEMANAL
// ====================================================================
async function loadHabitsAndSchedule() {
  const [habitsData, sched] = await Promise.all([
    apiGet("/api/habits"),
    apiGet("/api/schedule")
  ]);

  if (habitsData) {
    AppState.habits = habitsData;
    renderHabits(habitsData);
  }
  if (sched) {
    AppState.schedule = sched;
    renderSchedule(sched);
  }
}

function renderHabits(data) {
  const container = document.getElementById("habits-list-container");
  if (!container) return;
  container.innerHTML = "";

  document.getElementById("habit-streak-count").innerText = `${data.streak_days || 0} DÍAS`;
  document.getElementById("habit-best-streak").innerText = `Récord: ${data.best_streak || 0} Días`;

  (data.habits || []).forEach(h => {
    const item = document.createElement("div");
    item.className = `task-item ${h.completed ? 'completed' : ''}`;
    item.innerHTML = `
      <input type="checkbox" class="pixel-checkbox" ${h.completed ? 'checked' : ''}
             onchange="handleToggleHabit('${encodeURIComponent(h.raw)}', this.checked)">
      <div class="task-content">
        <span style="font-weight:bold;">${h.text}</span>
        ${(h.tags || []).map(t => `<span class="tag-badge">#${t}</span>`).join(" ")}
      </div>
    `;
    container.appendChild(item);
  });
}

async function handleToggleHabit(encodedRawText, completed) {
  const rawText = decodeURIComponent(encodedRawText);
  if (completed) {
    window.pixelFX.playSuccessSound();
    showToast("+50 XP Hábito diario completado!");
  } else {
    window.pixelFX.playBlip();
  }

  const res = await apiPost("/api/habits/toggle", {
    habit_text: rawText,
    completed: completed
  });

  if (res && res.success) {
    refreshAllData(false);
  }
}

function renderSchedule(sched) {
  const tbody = document.getElementById("schedule-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  sched.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="color:var(--retro-orange);">${row.Franja_Horaria || ""}</strong></td>
      <td>${row.Lunes_Miercoles || ""}</td>
      <td>${row.Jueves_Viernes || ""}</td>
      <td>${row.Sabado_Domingo || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ====================================================================
// MÓDULO 4: OBSIDIAN VAULT EXPLORER Y NOTAS
// ====================================================================
async function loadNotes() {
  const notes = await apiGet("/api/notes");
  if (!notes) return;
  AppState.notes = notes;
  renderNotes(notes);
}

function renderNotes(notes) {
  const container = document.getElementById("notes-container");
  if (!container) return;
  container.innerHTML = "";

  notes.forEach(note => {
    const card = document.createElement("div");
    card.className = "note-card";
    card.innerHTML = `
      <div>
        <h4>📄 ${note.title}</h4>
        <div class="note-preview">${note.preview}</div>
      </div>
      <div class="note-footer">
        <span style="color:#777; font-size:11px;">${note.created}</span>
        <div>
          <button class="pixel-btn btn-sm" onclick="openNoteViewer('${note.filename}')">Ver</button>
          <button class="pixel-btn btn-sm" style="border-color:var(--retro-red);" onclick="deleteNote('${note.filename}')">X</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function openAddNoteModal() {
  window.pixelFX.playKeyClick();
  document.getElementById("modal-add-note").classList.add("active");
}

async function submitAddNote(e) {
  e.preventDefault();
  const title = document.getElementById("note-modal-title").value;
  const content = document.getElementById("note-modal-content").value;
  const tagsStr = document.getElementById("note-modal-tags").value;
  const tags = tagsStr ? tagsStr.split(",").map(t => t.trim()) : ["nota"];

  const res = await apiPost("/api/notes", { title, content, tags });
  if (res && res.success) {
    closeModal("modal-add-note");
    document.getElementById("form-add-note").reset();
    window.pixelFX.playSuccessSound();
    showToast(`[OBSIDIAN] Nota guardada en Notas/${res.filename}`);
    loadNotes();
  }
}

function openNoteViewer(filename) {
  window.pixelFX.playKeyClick();
  const note = AppState.notes.find(n => n.filename === filename);
  if (!note) return;
  alert(`=== [OBSIDIAN NOTE: ${note.title}] ===\n\n${note.content}`);
}

async function deleteNote(filename) {
  if (!confirm(`¿Eliminar la nota ${filename} de la bóveda?`)) return;
  window.pixelFX.playKeyClick();
  const res = await apiDelete(`/api/notes?filename=${encodeURIComponent(filename)}`);
  if (res && res.success) {
    showToast(`[OBSIDIAN] Nota eliminada`);
    loadNotes();
  }
}

// ====================================================================
// MÓDULO 5: HISTORIAL SEMANAL Y RESETEO DE XP
// ====================================================================
const WEEKLY_MONTHS = [
  "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
  "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"
];

function formatWeekDate(value) {
  if (!value) return "—";
  const parts = String(value).split("-");
  if (parts.length !== 3) return value;
  const day = parseInt(parts[2], 10);
  const month = parseInt(parts[1], 10) - 1;
  return `${String(day).padStart(2, "0")} ${WEEKLY_MONTHS[month] || ""}`;
}

function formatWeekRange(start, end) {
  return `${formatWeekDate(start)} → ${formatWeekDate(end)}`;
}

function weeklyStatusLabel(status) {
  return status === "reset" ? "RESET" : "COMPLETED";
}

function weeklyModuleChips(breakdown) {
  const modules = [
    ["estudios", "💻", "ESTUDIOS"],
    ["rygon", "🎨", "RYGON"],
    ["rutinas", "⏰", "HÁBITOS"]
  ];
  return modules.map(([key, icon, label]) => {
    const bucket = (breakdown && breakdown[key]) || {};
    const total = Number(bucket.total || 0);
    const done = Number(bucket.completed || 0);
    const pct = total ? Math.round((done / total) * 100) : 0;
    return `<span class="module-chip" title="${label}: ${done}/${total}">${icon} ${label} ${done}/${total} · ${pct}%</span>`;
  }).join("");
}

async function loadWeeklyData() {
  const history = await apiGet("/api/weekly/history");
  const current = await apiGet("/api/weekly/current");

  if (history) {
    AppState.weeklyHistory = history.records || [];
    AppState.weeklyAggregates = history.aggregates || null;
    AppState.weeklySupabase = history.supabase || null;
    renderWeeklyHistory(history);

    const pending = history.pending_summary;
    if (
      pending &&
      !AppState.weeklySummaryOpen &&
      !AppState.weeklyAckedIds.has(pending.id)
    ) {
      openWeeklySummary(pending, true);
    }
  }

  if (current) {
    AppState.weeklyCurrent = current;
    renderWeeklyCurrent(current);
  }
}

function renderWeeklyCurrent(data) {
  const panel = document.getElementById("weekly-current-panel");
  if (!panel) return;

  const metrics = data.metrics || {};
  const period = data.period || {};
  const vault = metrics.vault || {};
  const pct = Number(metrics.effectiveness_percentage || 0);
  const days = Number(period.days_remaining || 0);
  const closeLabel = days <= 0
    ? "CIERRE PENDIENTE"
    : `CIERRA EN ${days} DÍA${days === 1 ? "" : "S"}`;
  const pctColor = pct >= 80
    ? "var(--retro-green)"
    : (pct >= 50 ? "var(--retro-orange)" : "var(--retro-red)");

  panel.innerHTML = `
    <div class="weekly-current-card">
      <div class="weekly-current-head">
        <div>
          <div class="weekly-cycle-label">CICLO ACTIVO // SEM ${period.week_number || "—"} · ${formatWeekRange(period.start, period.end)}</div>
          <div class="weekly-cycle-sub">${closeLabel} · ${data.auto_close_enabled ? "AUTO-CLOSE AL FINAL DEL CICLO" : "CIERRE MANUAL"}</div>
        </div>
        <div class="weekly-current-xp">+${metrics.xp_earned || 0}<span>XP SEMANA</span></div>
      </div>
      <div class="weekly-metric-row">
        <div class="weekly-metric"><span class="weekly-big">${metrics.completed_tasks || 0}/${metrics.total_tasks || 0}</span><small>TAREAS SEMANA</small></div>
        <div class="weekly-metric"><span class="weekly-big" style="color:${pctColor}">${pct}%</span><small>EFECTIVIDAD</small></div>
        <div class="weekly-metric"><span class="weekly-big">${metrics.pending_tasks || 0}</span><small>PENDIENTES</small></div>
        <div class="weekly-metric"><span class="weekly-big">${data.lifetime_xp || 0}</span><small>XP TOTAL</small></div>
      </div>
      <div class="weekly-progress"><div class="weekly-progress-fill" style="width:${Math.min(100, pct)}%"></div></div>
      <div class="weekly-vault-line">
        BÓVEDA COMPLETA: ${vault.completed || 0}/${vault.total || 0} TAREAS (${vault.effectiveness || 0}%)
        · NIVEL ${data.lifetime_level || 1}
        · ${data.xp_per_task || 25} XP/TAREA · ${data.xp_per_habit || 50} XP/HÁBITO
        · ${(data.supabase && data.supabase.configured) ? "☁️ SUPABASE MIRROR" : "💾 LOCAL ONLY"}
      </div>
      <div class="weekly-breakdown">${weeklyModuleChips(metrics.breakdown)}</div>
    </div>
  `;
}

function renderWeeklyAggregates(aggregates) {
  const grid = document.getElementById("weekly-lifetime-grid");
  if (!grid) return;
  if (!aggregates || !aggregates.total_weeks) {
    grid.innerHTML = "";
    return;
  }
  const best = aggregates.best_week || {};
  grid.innerHTML = `
    <div class="stat-card card-primary">
      <div class="stat-header"><span class="stat-label">Semanas Cerradas</span><span class="stat-icon">🗂️</span></div>
      <div class="stat-value">${aggregates.total_weeks}</div>
      <div class="stat-footer">${aggregates.completed_weeks || 0} completed · ${aggregates.reset_weeks || 0} reset</div>
    </div>
    <div class="stat-card card-success">
      <div class="stat-header"><span class="stat-label">XP Histórica</span><span class="stat-icon">⚡</span></div>
      <div class="stat-value" style="color:var(--retro-green);">${aggregates.total_xp || 0}</div>
      <div class="stat-footer">Acumulada en el historial</div>
    </div>
    <div class="stat-card card-blue">
      <div class="stat-header"><span class="stat-label">Efectividad Media</span><span class="stat-icon">📈</span></div>
      <div class="stat-value" style="color:var(--retro-blue);">${aggregates.avg_effectiveness || 0}%</div>
      <div class="stat-footer">Promedio de todos los ciclos</div>
    </div>
    <div class="stat-card">
      <div class="stat-header"><span class="stat-label">Mejor Semana</span><span class="stat-icon">🏆</span></div>
      <div class="stat-value" style="color:var(--retro-orange);">${best.effectiveness_percentage || 0}%</div>
      <div class="stat-footer">${formatWeekRange(best.week_start_date, best.week_end_date)}</div>
    </div>
  `;
}

function renderWeeklyHistory(history) {
  const grid = document.getElementById("weekly-history-grid");
  const count = document.getElementById("weekly-history-count");
  const records = history.records || [];

  if (count) {
    count.innerText = `${records.length} CICLO${records.length === 1 ? "" : "S"}`;
  }
  renderWeeklyAggregates(history.aggregates);

  if (!grid) return;
  if (!records.length) {
    grid.innerHTML = `
      <div class="weekly-empty">
        Aún no hay semanas cerradas. Usa "CERRAR SEMANA" para generar el primer registro.
      </div>
    `;
    return;
  }

  grid.innerHTML = records.map(record => {
    const pct = Number(record.effectiveness_percentage || 0);
    const status = record.status === "reset" ? "reset" : "completed";
    const synced = record.synced ? "☁️" : "💾";
    return `
      <article class="weekly-card ${status}">
        <div class="weekly-card-top">
          <span class="weekly-card-week">SEM ${record.week_number || "—"}</span>
          <span class="weekly-status ${status}">${weeklyStatusLabel(status)} ${synced}</span>
        </div>
        <div class="weekly-card-range">${formatWeekRange(record.week_start_date, record.week_end_date)}</div>
        <div class="weekly-card-score">${pct}%</div>
        <div class="weekly-card-label">EFECTIVIDAD</div>
        <div class="weekly-progress"><div class="weekly-progress-fill" style="width:${Math.min(100, pct)}%"></div></div>
        <div class="weekly-card-stats">
          <span>✅ ${record.completed_tasks || 0}/${record.total_tasks || 0}</span>
          <span>⚡ ${record.xp_earned || 0} XP</span>
        </div>
        <div class="weekly-card-breakdown">${weeklyModuleChips(record.breakdown)}</div>
        <button class="pixel-btn btn-sm" onclick="openWeeklySummaryById('${record.id}')">🔍 VER REPORTE</button>
      </article>
    `;
  }).join("");
}

function openWeeklySummaryById(recordId) {
  const record = (AppState.weeklyHistory || []).find(r => r.id === recordId);
  if (record) openWeeklySummary(record, false);
}

function openWeeklySummary(record, automatic = false) {
  if (!record) return;

  AppState.weeklySummaryOpen = true;
  AppState.weeklyAckedIds.add(record.id);
  apiPost("/api/weekly/ack", { id: record.id });

  const pct = Number(record.effectiveness_percentage || 0);
  const total = Number(record.total_tasks || 0);
  const completed = Number(record.completed_tasks || 0);
  const pending = record.pending_tasks !== undefined
    ? Number(record.pending_tasks)
    : Math.max(0, total - completed);
  const breakdown = record.breakdown || {};

  const moduleRows = [
    ["estudios", "💻", "ESTUDIOS"],
    ["rygon", "🎨", "RYGON STUDIO"],
    ["rutinas", "⏰", "HÁBITOS"]
  ].map(([key, icon, label]) => {
    const bucket = breakdown[key] || {};
    const moduleTotal = Number(bucket.total || 0);
    const moduleDone = Number(bucket.completed || 0);
    const modulePct = moduleTotal
      ? Math.round((moduleDone / moduleTotal) * 100)
      : 0;
    return `
      <div class="summary-breakdown-row">
        <div class="summary-breakdown-label">${icon} ${label}</div>
        <div class="summary-bar"><div style="width:${modulePct}%"></div></div>
        <div class="summary-breakdown-value">${moduleDone}/${moduleTotal} · ${modulePct}% · +${bucket.xp || 0} XP</div>
      </div>
    `;
  }).join("");

  const title = document.getElementById("weekly-summary-title");
  const body = document.getElementById("weekly-summary-body");
  if (title) {
    title.innerText = automatic
      ? "📊 SEMANA FINALIZADA // REPORTE AUTOMÁTICO"
      : "📊 REPORTE SEMANAL // THIAN-CORE";
  }

  if (body) {
    body.innerHTML = `
      <div class="weekly-summary-hero">
        <div class="weekly-summary-score">${pct}%</div>
        <div>
          <div class="weekly-summary-range">${formatWeekRange(record.week_start_date, record.week_end_date)}</div>
          <div class="weekly-summary-sub">
            SEM ${record.week_number || "—"} · ${weeklyStatusLabel(record.status)}
            · ${record.source === "auto" ? "CIERRE AUTOMÁTICO" : "CIERRE MANUAL"}
          </div>
        </div>
        <div class="weekly-summary-xp">+${record.xp_earned || 0} XP</div>
      </div>

      <div class="summary-grid">
        <div><span>${completed}</span><small>TAREAS COMPLETADAS</small></div>
        <div><span>${total}</span><small>TOTAL DEL CICLO</small></div>
        <div><span>${pending}</span><small>PENDIENTES</small></div>
      </div>

      <div class="summary-breakdown">
        <h4>RENDIMIENTO POR MÓDULO</h4>
        ${moduleRows}
      </div>

      <p class="weekly-summary-note">
        ${automatic
          ? "El ciclo se cerró automáticamente. El contador semanal ya está en 0 y tus cursos, hábitos y productos siguen intactos."
          : "Registro guardado. El contador semanal se reinició sin modificar la estructura de tu bóveda de Obsidian."}
      </p>
    `;
  }

  const modal = document.getElementById("modal-week-summary");
  if (modal) modal.classList.add("active");
  window.pixelFX.playSuccessSound();
}

function closeWeeklySummary() {
  window.pixelFX.playKeyClick();
  const modal = document.getElementById("modal-week-summary");
  if (modal) modal.classList.remove("active");
  AppState.weeklySummaryOpen = false;
}

function openCloseWeekModal() {
  window.pixelFX.playKeyClick();
  const data = AppState.weeklyCurrent;
  const preview = document.getElementById("weekly-close-preview");

  if (!data) {
    showToast("No se pudo cargar el ciclo actual. Sincroniza e intenta de nuevo.", "error");
    return;
  }

  const metrics = data.metrics || {};
  const pct = Number(metrics.effectiveness_percentage || 0);
  if (preview) {
    preview.innerHTML = `
      <div class="weekly-close-preview">
        <div class="weekly-cycle-label">${formatWeekRange(data.period.start, data.period.end)}</div>
        <div class="weekly-close-numbers">
          <div><span>${metrics.completed_tasks || 0}/${metrics.total_tasks || 0}</span><small>TAREAS</small></div>
          <div><span>${pct}%</span><small>EFECTIVIDAD</small></div>
          <div><span>+${metrics.xp_earned || 0}</span><small>XP</small></div>
        </div>
      </div>
    `;
  }

  const force = document.getElementById("weekly-close-force");
  if (force) force.checked = false;
  const status = document.getElementById("weekly-close-status");
  if (status) status.value = "completed";

  const modal = document.getElementById("modal-close-week");
  if (modal) modal.classList.add("active");
}

async function confirmCloseWeek() {
  const button = document.getElementById("btn-confirm-close-week");
  const statusSelect = document.getElementById("weekly-close-status");
  const forceCheckbox = document.getElementById("weekly-close-force");
  const status = statusSelect ? statusSelect.value : "completed";
  const force = forceCheckbox ? forceCheckbox.checked : false;

  if (button) {
    button.disabled = true;
    button.innerText = "GUARDANDO...";
  }

  const result = await apiPost("/api/weekly/close", { status, force });

  if (button) {
    button.disabled = false;
    button.innerText = "CONFIRMAR CIERRE";
  }

  if (!result) return;

  if (!result.closed) {
    if (result.reason === "already_closed") {
      showToast("[WEEKLY] Ya existe un registro para este periodo.", "info");
    } else if (result.reason === "empty_week") {
      showToast("[WEEKLY] No hay tareas nuevas para cerrar. Marca tareas o usa 'Forzar'.", "info");
    } else {
      showToast(`[WEEKLY] Cierre cancelado: ${result.reason || "desconocido"}`, "error");
    }
    return;
  }

  closeModal("modal-close-week");
  window.pixelFX.playSuccessSound();
  showToast(
    `[WEEKLY] Semana cerrada: ${result.record.completed_tasks}/${result.record.total_tasks} tareas · +${result.record.xp_earned} XP`
  );

  // Evita que loadWeeklyData abra el modal automático y luego lo abramos
  // otra vez manualmente con el mismo registro.
  AppState.weeklyAckedIds.add(result.record.id);
  await loadWeeklyData();
  openWeeklySummary(result.record, false);
}

async function syncWeeklyCloud() {
  window.pixelFX.playKeyClick();
  const result = await apiPost("/api/weekly/sync", {});
  if (!result) return;

  if (!result.configured) {
    showToast(
      "[SUPABASE] Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (o usa config.json) para activar el respaldo.",
      "info"
    );
    return;
  }

  if (result.synced > 0) {
    window.pixelFX.playSuccessSound();
    showToast(`[SUPABASE] ${result.synced} registro(s) sincronizado(s).`);
  } else if (result.pending > 0) {
    showToast(
      `[SUPABASE] ${result.pending} registro(s) pendientes. Revisa la tabla weekly_history y las políticas RLS.`,
      "error"
    );
  } else {
    showToast("[SUPABASE] Todo el historial ya está respaldado.", "info");
  }

  await loadWeeklyData();
}

// ====================================================================
// MODALES Y PESTAÑAS (TABS ROUTING)
// ====================================================================
function switchTab(tabId) {
  window.pixelFX.playKeyClick();
  AppState.currentTab = tabId;

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  document.querySelectorAll(".tab-content-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === `tab-${tabId}`);
  });
}

function switchRygonSubtab(subtabId) {
  window.pixelFX.playKeyClick();
  AppState.currentRygonSubtab = subtabId;

  document.querySelectorAll(".subtab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.subtab === subtabId);
  });

  document.querySelectorAll(".rygon-subpanel").forEach(panel => {
    panel.style.display = panel.id === `rygon-${subtabId}` ? "block" : "none";
  });
}

function togglePendingFilter() {
  window.pixelFX.playKeyClick();
  AppState.filterOnlyPending = !AppState.filterOnlyPending;
  const btn = document.getElementById("btn-filter-pending");
  if (btn) {
    btn.classList.toggle("btn-green", AppState.filterOnlyPending);
    btn.innerText = AppState.filterOnlyPending ? "⏳ SOLO PENDIENTES [ON]" : "⏳ FILTRO PENDIENTES";
  }
  renderStudies(AppState.studies);
  renderWorkshop(AppState.workshop);
}

function closeModal(modalId) {
  window.pixelFX.playKeyClick();
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

function toggleSoundButton() {
  const isEnabled = window.pixelFX.toggleSound();
  const btn = document.getElementById("btn-sound-toggle");
  if (btn) {
    btn.innerText = isEnabled ? "🔊 AUDIO: ON" : "🔇 AUDIO: OFF";
  }
}

// ====================================================================
// INICIALIZACIÓN
// ====================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar estado del botón de sonido
  const soundBtn = document.getElementById("btn-sound-toggle");
  if (soundBtn) {
    soundBtn.innerText = window.pixelFX.soundEnabled ? "🔊 AUDIO: ON" : "🔇 AUDIO: OFF";
  }

  // Carga de datos inicial
  refreshAllData(false);

  // Polling automático cada 6 segundos para detectar cambios externos de Obsidian
  setInterval(() => {
    refreshAllData(false);
  }, 6000);
});
