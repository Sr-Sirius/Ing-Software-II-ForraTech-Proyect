import { initFlash } from "./core/flash.js";
import { initGlow } from "./core/glow.js";
import { initReveal } from "./core/reveal.js";

import { initNavbar } from "./layout/navbar.js";
import { initSidebar } from "./layout/sidebar.js";

document.addEventListener("DOMContentLoaded", () => {

    initFlash();
    initGlow();
    initReveal();

    initNavbar();
    initSidebar();

});