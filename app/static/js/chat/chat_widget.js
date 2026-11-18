// Chat web de soporte — comunicación sincrónica (JavaScript ↔ Flask).
//
// 1. El visitante escribe → fetch POST /chat/api/messages (JSON sobre HTTPS).
// 2. Flask guarda el mensaje y lo publica en el grupo de Telegram del equipo.
// 3. Un integrante responde en Telegram → webhook → Flask guarda la respuesta.
// 4. Este script consulta GET /chat/api/messages?after=<id> cada 3 s (polling)
//    mientras el panel está abierto, y cada 20 s si está cerrado.

const OPEN_INTERVAL = 3000;
const CLOSED_INTERVAL = 20000;
const NAME_KEY = "forratech_chat_name";

export function initChatWidget() {
    const root = document.getElementById("chat-widget");
    if (!root) return;

    const api = root.dataset.api;
    const launcher = document.getElementById("cw-launcher");
    const panel = document.getElementById("cw-panel");
    const closeBtn = document.getElementById("cw-close");
    const list = document.getElementById("cw-messages");
    const form = document.getElementById("cw-form");
    const nameInput = document.getElementById("cw-name");
    const textInput = document.getElementById("cw-text");
    const unreadBadge = document.getElementById("cw-unread");

    let lastId = 0;
    let hasSession = false;
    let open = false;
    let timer = null;
    let unread = 0;
    let sending = false;

    try {
        nameInput.value = localStorage.getItem(NAME_KEY) || "";
    } catch (_) { /* almacenamiento no disponible */ }

    const formatTime = (ts) =>
        new Date(ts * 1000).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });

    function render(msg) {
        const li = document.createElement("li");
        li.className = `cw-msg ${msg.sender}`;

        if (msg.sender !== "system") {
            const meta = document.createElement("span");
            meta.className = "cw-meta";
            const via = msg.channel === "telegram" ? " · vía Telegram" : "";
            meta.textContent = `${msg.author}${via} · ${formatTime(msg.created_at)}`;
            li.appendChild(meta);
        }
        const p = document.createElement("p");
        p.textContent = msg.text; // textContent evita inyección de HTML
        li.appendChild(p);
        list.appendChild(li);
    }

    function scrollDown() {
        list.scrollTop = list.scrollHeight;
    }

    function setUnread(n) {
        unread = n;
        unreadBadge.hidden = n === 0;
        unreadBadge.textContent = String(n);
    }

    async function poll() {
        try {
            const res = await fetch(`${api}?after=${lastId}`, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            if (!res.ok) return;
            const data = await res.json();
            hasSession = Boolean(data.session);
            if (hasSession) nameInput.hidden = true;

            let newFromTeam = 0;
            for (const msg of data.messages) {
                render(msg);
                lastId = Math.max(lastId, msg.id);
                if (msg.sender === "agent") newFromTeam += 1;
            }
            if (data.messages.length) {
                scrollDown();
                if (!open && newFromTeam) setUnread(unread + newFromTeam);
            }
        } catch (_) {
            /* sin conexión: se reintenta en el siguiente ciclo */
        }
    }

    function schedule() {
        clearTimeout(timer);
        // Sin conversación iniciada no hace falta consultar con el panel cerrado.
        if (!open && !hasSession) return;
        timer = setTimeout(async () => {
            await poll();
            schedule();
        }, open ? OPEN_INTERVAL : CLOSED_INTERVAL);
    }

    function toggle(force) {
        open = typeof force === "boolean" ? force : !open;
        panel.hidden = !open;
        launcher.setAttribute("aria-expanded", String(open));
        root.classList.toggle("is-open", open);
        if (open) {
            setUnread(0);
            poll().then(scrollDown);
            (hasSession ? textInput : (nameInput.value ? textInput : nameInput)).focus();
        }
        schedule();
    }

    async function send(event) {
        event.preventDefault();
        const text = textInput.value.trim();
        if (!text || sending) return;

        sending = true;
        form.classList.add("is-sending");
        try {
            const name = nameInput.value.trim();
            try { if (name) localStorage.setItem(NAME_KEY, name); } catch (_) {}

            const res = await fetch(api, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ name, text }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                render({ sender: "system", text: data.error || "No se pudo enviar el mensaje." });
                scrollDown();
                return;
            }
            textInput.value = "";
            await poll();
            schedule();
        } catch (_) {
            render({ sender: "system", text: "Sin conexión. Intenta de nuevo." });
            scrollDown();
        } finally {
            sending = false;
            form.classList.remove("is-sending");
        }
    }

    launcher.addEventListener("click", () => toggle());
    closeBtn.addEventListener("click", () => toggle(false));
    form.addEventListener("submit", send);
    textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && open) toggle(false);
    });
    document.querySelectorAll("[data-open-chat]").forEach((btn) =>
        btn.addEventListener("click", () => toggle(true))
    );

    // Si ya había una conversación (cookie de sesión), recuperarla.
    poll().then(schedule);
}
