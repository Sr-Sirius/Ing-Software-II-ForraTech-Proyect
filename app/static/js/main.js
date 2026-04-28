document.addEventListener("DOMContentLoaded", () => {

  function removeFlash(el) {
    el.style.transition = "all 0.4s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-10px) scale(0.95)";
    setTimeout(() => el.remove(), 400);
  }

  // AUTO-HIDE
  setTimeout(() => {
    const flashes = document.querySelectorAll(".flash");
    if (!flashes.length) return;

    flashes.forEach(el => removeFlash(el));
  }, 4000);

  // CLOSE BUTTON
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("close-flash")) {
      removeFlash(e.target.parentElement);
    }
  });

  // NAVBAR SCROLL
  window.addEventListener("scroll", () => {
    const navbar = document.querySelector(".navbar");
    if (!navbar) return;

    if (window.scrollY > 50) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  });

});