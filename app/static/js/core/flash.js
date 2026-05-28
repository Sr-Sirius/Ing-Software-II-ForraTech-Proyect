export function initFlash() {

    function removeFlash(el) {
        el.style.transition = "all 0.4s ease";
        el.style.opacity = "0";
        el.style.transform = "translateY(-10px) scale(0.95)";
        setTimeout(() => el.remove(), 400);
    }

    setTimeout(() => {
        document.querySelectorAll(".flash").forEach(removeFlash);
    }, 4000);

    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("close-flash")) {
            removeFlash(e.target.parentElement);
        }
    });
}