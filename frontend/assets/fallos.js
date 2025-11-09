
// UI para "Proyección de Fallos" con la misma interfaz (reutiliza el modal existente)
(function() {
  const API_BASE = "/api";

  function ensureCard() {
    const container = document.getElementById("cardsContainer") || document.querySelector("[data-calc-grid]") || document.body;
    if (document.getElementById("card-fallos")) return;

    // Crear tarjeta visual similar a las demás
    const card = document.createElement("div");
    card.id = "card-fallos";
    card.className = "glass-effect p-6 rounded-3xl hover:scale-[1.01] transition cursor-pointer";
    card.innerHTML = `
      <div class="flex items-center gap-3 mb-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-600/30 flex items-center justify-center">
          <span class="text-indigo-300 font-bold">FX</span>
        </div>
        <span class="text-indigo-400 text-sm font-medium">SALUD</span>
      </div>
      <h3 class="text-xl font-semibold text-white mb-1">Proyección de Fallos</h3>
      <p class="text-gray-300 text-sm">Riesgo de falla si NO haces el servicio</p>
    `;
    card.addEventListener("click", () => openCalculator('fallos'));
    container.appendChild(card);
  }

  function buildForm() {
    return `
      <form id="fallos-form" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-300 mb-1">Autoparte</label>
            <select id="fallos-part" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none">
              <option value="aceite">Aceite del motor</option>
              <option value="frenos">Pastillas de freno</option>
              <option value="correa">Correa de distribución</option>
              <option value="bateria">Batería</option>
              <option value="neumaticos">Neumáticos</option>
              <option value="filtro_aire">Filtro de aire</option>
              <option value="refrigerante_mangueras">Refrigerante / mangueras</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Clima</label>
            <select id="fallos-clima" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none">
              <option value="">—</option>
              <option value="templado">Templado</option>
              <option value="calido">Cálido</option>
              <option value="frio">Frío</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm text-gray-300 mb-1">Km actual</label>
            <input id="fallos-current-km" type="number" min="0" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" required />
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Km último servicio</label>
            <input id="fallos-last-km" type="number" min="0" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" required />
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Intervalo (km)</label>
            <input id="fallos-interval-km" type="number" min="1" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" required />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm text-gray-300 mb-1">Meses desde servicio (opcional)</label>
            <input id="fallos-months" type="number" min="0" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" />
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Intervalo (meses, opcional)</label>
            <input id="fallos-interval-months" type="number" min="1" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" />
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Horizonte (km, opcional)</label>
            <input id="fallos-horizon-km" type="number" min="1" class="w-full rounded-xl bg-black/20 text-white p-3 outline-none" />
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button id="fallos-submit" class="px-4 py-2 rounded-xl bg-indigo-600 text-white">Calcular proyección</button>
          <button id="fallos-agendar" type="button" class="px-4 py-2 rounded-xl bg-emerald-600 text-white hidden">Agendar en Google Calendar</button>
        </div>
      </form>
      <div id="fallos-result" class="mt-6 space-y-4 hidden">
        <img id="fallos-img" alt="Gráfica de riesgo" class="rounded-xl w-full max-h-[420px] object-contain bg-black/10" />
        <div id="fallos-resumen" class="text-gray-300 text-sm"></div>
      </div>
    `;
  }

  async function postJSON(path, data) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail?.detail || "Error al procesar la solicitud");
    }
    return res.json();
  }

  function renderFallosModal() {
    const modal = document.getElementById('calculatorModal');
    const title = document.getElementById('modalTitle');
    const content = document.getElementById('modalContent');

    if (!modal || !title || !content) return;

    title.textContent = 'Proyección de Fallos';
    content.innerHTML = buildForm();
    modal.classList.remove('hidden');

    const form = document.getElementById('fallos-form');
    const btn = document.getElementById('fallos-submit');
    const btnCal = document.getElementById('fallos-agendar');
    const resBox = document.getElementById('fallos-result');
    const img = document.getElementById('fallos-img');
    const resumen = document.getElementById('fallos-resumen');

    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const payload = {
        part_type: document.getElementById('fallos-part').value,
        current_km: parseFloat(document.getElementById('fallos-current-km').value),
        last_service_km: parseFloat(document.getElementById('fallos-last-km').value),
        service_interval_km: parseFloat(document.getElementById('fallos-interval-km').value),
        months_since_service: document.getElementById('fallos-months').value ? parseFloat(document.getElementById('fallos-months').value) : null,
        service_interval_months: document.getElementById('fallos-interval-months').value ? parseFloat(document.getElementById('fallos-interval-months').value) : null,
        clima: document.getElementById('fallos-clima').value || null,
        horizon_km: document.getElementById('fallos-horizon-km').value ? parseFloat(document.getElementById('fallos-horizon-km').value) : null,
      };
      try {
        const data = await postJSON("/fallos/proyeccion", payload);
        img.src = data.chart_url;
        resBox.classList.remove('hidden');
        resumen.textContent = `Riesgo próximo 1/3/6 meses (si aplica): ${data.temporal ? (data.temporal.risk_next_1m_pct + "% / " + data.temporal.risk_next_3m_pct + "% / " + data.temporal.risk_next_6m_pct + "%") : "N/A"} `;
        btnCal.classList.remove('hidden');
        // Guardar detalles para agendar
        btnCal.dataset.summary = `Servicio de ${payload.part_type} (proyección de fallos)`;
        btnCal.dataset.description = `Proyección generada. Intervalo ${payload.service_interval_km} km. Imagen: ${data.chart_url}`;
      } catch (err) {
        alert(err.message);
      }
    });

    btnCal.addEventListener('click', async () => {
      const now = new Date();
      const start = new Date(now.getTime() + 48*60*60*1000); // +48h por defecto
      const end = new Date(start.getTime() + 60*60*1000);
      const payload = {
        summary: btnCal.dataset.summary || "Servicio automotriz",
        description: btnCal.dataset.description || "",
        start_iso: start.toISOString().slice(0,19),
        end_iso: end.toISOString().slice(0,19),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "America/Mexico_City",
        reminder_minutes: 60,
      };
      try {
        const resp = await postJSON("/calendar/agendar", payload);
        if (resp.status === "created") {
          alert("Evento creado correctamente. Revisa tu Google Calendar.");
        } else if (resp.status === "not_configured") {
          alert("Google Calendar no está configurado aún. Sigue las instrucciones en README.");
          console.log(resp.how_to_enable);
        } else {
          alert(resp.detail || "No se pudo agendar.");
        }
      } catch (e) {
        alert(e.message);
      }
    });
  }

  // Hook en openCalculator existente; si no existe, crea un fallback básico
  const originalOpen = window.openCalculator;
  window.openCalculator = function(type) {
    if (type === 'fallos') {
      renderFallosModal();
      return;
    }
    if (typeof originalOpen === 'function') {
      return originalOpen.apply(this, arguments);
    }
  };

  // Inyectar tarjeta al cargar
  document.addEventListener('DOMContentLoaded', ensureCard);
})();
