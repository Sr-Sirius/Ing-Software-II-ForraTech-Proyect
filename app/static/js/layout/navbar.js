export function initNavbar() {

    const burger = document.getElementById("burger");

    if (burger) {
        burger.addEventListener("click", () => {
            document.body.classList.toggle("open");
        });
    }

    // dropdown
    document.querySelectorAll(".dropdown > button").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();

            const parent = btn.parentElement;

            document.querySelectorAll(".dropdown").forEach(d => {
                if (d !== parent) d.classList.remove("active");
            });

            parent.classList.toggle("active");
        });
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".dropdown")) {
            document.querySelectorAll(".dropdown").forEach(d => {
                d.classList.remove("active");
            });
        }
    });

    // scroll effect
    window.addEventListener("scroll", () => {
        const navbar = document.querySelector(".navbar");
        if (!navbar) return;

        navbar.classList.toggle("scrolled", window.scrollY > 50);
    });
}