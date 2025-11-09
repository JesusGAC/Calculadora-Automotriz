
// Funciones utilitarias para calendario (puede ser usado también por otras calculadoras)
window.agendarServicio = async function({summary, description, start, end, timezone, reminder_minutes=60}) {
  try {
    const payload = {
      summary,
      description: description || "",
      start_iso: start.toISOString().slice(0,19),
      end_iso: end.toISOString().slice(0,19),
      timezone: timezone || (Intl.DateTimeFormat().resolvedOptions().timeZone || "America/Mexico_City"),
      reminder_minutes
    };
    const res = await fetch("/api/calendar/agendar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "created") {
      alert("Evento creado en Google Calendar.");
    } else if (data.status === "not_configured") {
      alert("Google Calendar no está configurado. Revisa README para configurarlo.");
      console.log(data.how_to_enable);
    } else {
      alert(data.detail || "No se pudo agendar.");
    }
    return data;
  } catch (e) {
    alert(e.message);
    return { status: "error", detail: e.message };
  }
}
