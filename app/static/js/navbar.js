document.addEventListener("DOMContentLoaded", () => {

    const burger = document.getElementById("burger");

    if (burger) {
        burger.addEventListener("click", () => {
            document.body.classList.toggle("open");
        });
    }

    // 🔽 DROPDOWN CLICK (mobile)
    document.querySelectorAll(".dropdown > button").forEach(btn => {

    btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        const parent = btn.parentElement;

        // cerrar otros
        document.querySelectorAll(".dropdown").forEach(d => {
            if (d !== parent) d.classList.remove("active");
        });

        parent.classList.toggle("active");
    });

});

    // 🔥 CERRAR AL HACER CLICK FUERA
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".dropdown")) {
            document.querySelectorAll(".dropdown").forEach(d => {
                d.classList.remove("active");
            });
        }
    });

});