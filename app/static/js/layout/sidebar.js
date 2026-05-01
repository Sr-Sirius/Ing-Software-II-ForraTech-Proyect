export function initSidebar() {

    const sidebar = document.querySelector(".sidebar");
    const handle = document.querySelector(".handle");
    const main = document.querySelector("main");

    let isResizing = false;

    const MIN = 70;
    const MAX = 260;

    if (!sidebar || !handle || !main) return;

    handle.addEventListener("mousedown", () => {
        isResizing = true;
        document.body.classList.add("resizing");
    });

    document.addEventListener("mousemove", (e) => {
        if (!isResizing) return;

        let newWidth = e.clientX - sidebar.getBoundingClientRect().left;

        if (newWidth < MIN) newWidth = MIN;
        if (newWidth > MAX) newWidth = MAX;

        sidebar.style.width = newWidth + "px";
        main.style.marginLeft = (newWidth + 40) + "px";

        if (newWidth < 110) {
            sidebar.classList.add("collapsed");
        } else {
            sidebar.classList.remove("collapsed");
        }
    });

    document.addEventListener("mouseup", () => {
        if (!isResizing) return;

        isResizing = false;
        document.body.classList.remove("resizing");

        const width = sidebar.offsetWidth;

        if (width < 110) {
            sidebar.style.width = "80px";
            sidebar.classList.add("collapsed");
            main.style.marginLeft = "120px";
        } else {
            sidebar.style.width = "240px";
            sidebar.classList.remove("collapsed");
            main.style.marginLeft = "280px";
        }
    });
}