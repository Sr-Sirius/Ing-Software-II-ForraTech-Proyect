document.addEventListener("DOMContentLoaded", () => {

    const email = document.getElementById("email");
    const terms = document.getElementById("terms");
    const confirmPassword = document.getElementById("confirm-password");

    const form = document.querySelector(".register-form");

    if (!form) return;

    // EMAIL VALIDATION
    if (email) {
        email.addEventListener("input", () => {
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            email.classList.toggle("valid", regex.test(email.value));
            email.classList.toggle("invalid", !regex.test(email.value));
        });
    }

    // SUBMIT
    form.addEventListener("submit", (e) => {

        const emailValid = email?.classList.contains("valid");
        const passwordValid = confirmPassword?.classList.contains("valid");
        const termsAccepted = terms?.checked;

        if (!emailValid || !passwordValid || !termsAccepted) {
            e.preventDefault();
            alert("Please complete the form correctly.");
        }

    });

});