// cloudflare/worker.js
// ─────────────────────────────────────────────────────────────────────────────
// Segundo punto de acceso a ForraTech con OTRO certificado TLS (gratis).
//
// Render no permite cargar certificados propios: siempre presenta el suyo
// (Let's Encrypt / Google Trust Services). Este Worker de Cloudflare publica
// la misma aplicación en https://<nombre>.<tu-subdominio>.workers.dev con el
// certificado del borde de Cloudflare, y reenvía cada petición a Render.
//
//   Navegador ──TLS #1 (cert. Cloudflare)──> Cloudflare Worker
//             ──TLS #2 (cert. Render)──────> Render ──> Gunicorn ──> Flask
//
// Despliegue (5 minutos, sin tarjeta):
//   1. Crear cuenta gratis en https://dash.cloudflare.com
//   2. Workers & Pages → Create → "Hello World" Worker → nombre: forratech
//   3. Edit code → pegar este archivo → Deploy
//   4. Abrir https://forratech.<tu-subdominio>.workers.dev
// ─────────────────────────────────────────────────────────────────────────────

const ORIGIN = "https://ing-software-ii-forratech-proyect.onrender.com";

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, ORIGIN);

    const headers = new Headers(request.headers);
    headers.set("X-Forwarded-Host", incoming.host);
    headers.set("X-ForraTech-Edge", "cloudflare-worker");

    const init = {
      method: request.method,
      headers,
      redirect: "manual",
    };
    if (!["GET", "HEAD"].includes(request.method)) {
      init.body = await request.arrayBuffer();
    }

    const upstream = await fetch(target.toString(), init);
    const response = new Response(upstream.body, upstream);

    // Si Render redirige con URL absoluta, mantener al usuario en el Worker.
    const location = response.headers.get("Location");
    if (location && location.startsWith(ORIGIN)) {
      response.headers.set(
        "Location",
        location.replace(ORIGIN, `https://${incoming.host}`)
      );
    }

    response.headers.set("X-Served-By", "Cloudflare Worker → Render");
    return response;
  },
};
