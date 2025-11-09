
const API_BASE = "/api";

async function apiPost(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const msg = detail?.detail || "Error al procesar la solicitud";
    throw new Error(msg);
  }
  return res.json();
}

// ---------------- Servicio ----------------
window.calcServicio = async function () {
  const current_km = parseFloat(document.getElementById("svc-current-km").value || "0");
  const last_service_km = parseFloat(document.getElementById("svc-last-service-km").value || "0");
  const service_interval_km = parseFloat(document.getElementById("svc-interval-km").value || "0");
  const avg_km_per_month = parseFloat(document.getElementById("svc-avg-km-month").value || "0");

  try {
    const data = await apiPost("/servicio/calculate", {
      current_km, last_service_km, service_interval_km, avg_km_per_month
    });

    const kmText = `${data.km_remaining.toLocaleString()} km`;
    document.getElementById("svc-km-remaining").textContent = data.is_overdue ? `Atrasado por ${kmText}` : kmText;
    document.getElementById("svc-days-remaining").textContent = data.days_to_service !== null ? `${data.days_to_service} días` : "-- días";
    document.getElementById("svc-date-estimated").textContent = data.estimated_date ? `Fecha estimada: ${data.estimated_date}` : "";
    document.getElementById("svc-message").textContent = data.message;
    document.getElementById("svc-warnings").textContent = "";
  } catch (err) {
    document.getElementById("svc-warnings").textContent = `⚠️ ${err.message}`;
  }
};

// ---------------- Consumo ----------------
window.calcConsumo = async function () {
  const distance_km = parseFloat(document.getElementById("cons-distance").value || "0");
  const liters = parseFloat(document.getElementById("cons-liters").value || "0");
  const price_per_liter = parseFloat(document.getElementById("cons-price").value || "0");
  const driving_type = document.getElementById("cons-driving-type").value;

  try {
    const data = await apiPost("/consumo/calculate", {
      distance_km, liters, price_per_liter, driving_type
    });
    document.getElementById("cons-kmpl").textContent = `${data.km_per_liter} km/L`;
    document.getElementById("cons-cost-per-km").textContent = `$${data.cost_per_km} /km`;
    document.getElementById("cons-total").textContent = `$${data.total_cost}`;
    document.getElementById("cons-co2").textContent = `${data.co2_kg} kg CO₂`;
    document.getElementById("cons-rating").textContent = `${data.rating_text} (típico ${data.typical_km_per_liter} km/L)`;
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

// ---------------- Batería ----------------
window.evaluateBateria = async function () {
  const install_date = document.getElementById("bat-install").value;
  const battery_type = document.getElementById("bat-type").value;
  const usage = document.getElementById("bat-usage").value;
  const climate = document.getElementById("bat-climate").value;

  try {
    const data = await apiPost("/bateria/evaluate", {
      install_date, battery_type, usage, climate
    });
    document.getElementById("bat-percent").textContent = `${data.percent_remaining}%`;
    document.getElementById("bat-months-left").textContent = `${data.months_left} meses`;
    document.getElementById("bat-status").textContent = `Estado: ${data.status}. Vida base: ${data.base_months} meses, Ajustada: ${data.adjusted_total_months} meses.`;

    const recoUl = document.getElementById("bat-reco");
    recoUl.innerHTML = "";
    data.recommendations.forEach(r => {
      const li = document.createElement("li");
      li.textContent = `• ${r}`;
      recoUl.appendChild(li);
    });
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

// ---------------- Tips ----------------
window.showTips = async function (category) {
  try {
    const res = await fetch(`${API_BASE}/tips/${category}`);
    const data = await res.json();
    const cont = document.getElementById("tipsContent");
    cont.innerHTML = "";
    data.items.forEach(item => {
      const div = document.createElement("div");
      div.className = "p-4 bg-white bg-opacity-5 rounded-lg";
      div.innerHTML = `<h4 class="font-semibold text-green-400 mb-2">• ${item.title}</h4>
                       <p class="text-sm text-gray-300">${item.body}</p>`;
      cont.appendChild(div);
    });
  } catch (err) {
    console.error(err);
  }
};

// ---------------- Autopartes ----------------
window.searchParts = async function () {
  const brand = document.getElementById("parts-brand").value;
  const model = document.getElementById("parts-model").value;
  const yearStr = document.getElementById("parts-year").value;
  const part_type = document.getElementById("parts-type").value;

  const year = yearStr ? parseInt(yearStr) : null;

  try {
    const data = await apiPost("/autopartes/search", {
      brand, model, year, part_type
    });
    const results = document.getElementById("partsResults");
    results.innerHTML = `<div class="text-sm text-gray-300">Consulta generada: <span class="font-semibold">${data.query || '(genérica)'}</span></div>`;
    data.links.forEach(link => {
      const a = document.createElement("a");
      a.href = link.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "block p-3 bg-blue-500 bg-opacity-10 hover:bg-opacity-20 rounded-lg text-white";
      a.textContent = `🔎 ${link.site}`;
      results.appendChild(a);
    });
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

// ---------------- Depreciación ----------------
window.calcDepreciacion = async function () {
  const purchase_price = parseFloat(document.getElementById("dep-price").value || "0");
  const purchase_year = parseInt(document.getElementById("dep-year").value || "0");
  const current_km = parseFloat(document.getElementById("dep-km").value || "0");
  const condition = document.getElementById("dep-condition").value;
  const brand_class = document.getElementById("dep-brand").value;

  try {
    const data = await apiPost("/depreciacion/calculate", {
      purchase_price, purchase_year, current_km, condition, brand_class
    });

    document.getElementById("dep-value").textContent = `$${data.estimated_value.toLocaleString()}`;
    document.getElementById("dep-percent").textContent = `${data.depreciation_percent}%`;
    document.getElementById("dep-annual").textContent = `$${data.annual_loss_avg.toLocaleString()} /año`;

    const bd = data.breakdown;
    const ul = document.getElementById("dep-breakdown");
    ul.innerHTML = "";
    const items = [
      `Edad (años): ${bd.age_years}`,
      `Factor residual base: ${bd.base_residual_factor}`,
      `Marca (factor): ${bd.brand_factor}`,
      `Condición (factor): ${bd.condition_factor}`,
      `Kilometraje (factor): ${bd.mileage_factor}`,
      `Factor residual final: ${bd.final_residual_factor}`,
    ];
    items.forEach(t => {
      const li = document.createElement("li");
      li.textContent = `• ${t}`;
      ul.appendChild(li);
    });
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};
