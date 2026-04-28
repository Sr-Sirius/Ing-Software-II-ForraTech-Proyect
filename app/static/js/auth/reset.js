document.addEventListener("DOMContentLoaded", () => {

    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");
    const errorMessage = document.getElementById("error-message");

    const form = document.querySelector(".register-form");

    if (!form) return;

    form.addEventListener("submit", (e) => {

        if (password.value !== confirmPassword.value) {
            e.preventDefault();

            if (errorMessage) {
                errorMessage.textContent = "Passwords do not match";
                errorMessage.classList.add("active");
            }
        }

    });

});