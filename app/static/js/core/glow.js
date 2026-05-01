export function initGlow() {

    document.querySelectorAll(".glow-hover").forEach(el => {
        el.addEventListener("mousemove", e => {
            const rect = el.getBoundingClientRect();

            el.style.setProperty("--x", `${e.clientX - rect.left}px`);
            el.style.setProperty("--y", `${e.clientY - rect.top}px`);
        });
    });

}