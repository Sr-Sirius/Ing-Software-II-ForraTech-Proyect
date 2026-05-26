const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm-password");
const rulesBox = document.getElementById("password-rules");
const errorMessage = document.getElementById("error-message");

// REGLAS
const ruleLength = document.getElementById("rule-length");
const ruleUpper = document.getElementById("rule-uppercase");
const ruleNumber = document.getElementById("rule-number");
const ruleSpecial = document.getElementById("rule-special");

// MOSTRAR REGLAS AL FOCUS
password.addEventListener("focus", () => {
    rulesBox.classList.add("active");
});

// VALIDACIÓN EN TIEMPO REAL
password.addEventListener("input", () => {
    const value = password.value;

    // LENGTH
    if (value.length >= 6) {
        ruleLength.classList.add("valid");
        ruleLength.classList.remove("invalid");
    } else {
        ruleLength.classList.add("invalid");
        ruleLength.classList.remove("valid");
    }

    // UPPERCASE
    if (/[A-Z]/.test(value)) {
        ruleUpper.classList.add("valid");
        ruleUpper.classList.remove("invalid");
    } else {
        ruleUpper.classList.add("invalid");
        ruleUpper.classList.remove("valid");
    }

    // NUMBER
    if (/[0-9]/.test(value)) {
        ruleNumber.classList.add("valid");
        ruleNumber.classList.remove("invalid");
    } else {
        ruleNumber.classList.add("invalid");
        ruleNumber.classList.remove("valid");
    }

    // SPECIAL
    if (/[^A-Za-z0-9]/.test(value)) {
        ruleSpecial.classList.add("valid");
        ruleSpecial.classList.remove("invalid");
    } else {
        ruleSpecial.classList.add("invalid");
        ruleSpecial.classList.remove("valid");
    }
});

// CONFIRM PASSWORD
confirmPassword.addEventListener("input", () => {
    if (confirmPassword.value === password.value && confirmPassword.value !== "") {
        confirmPassword.classList.add("valid");
        confirmPassword.classList.remove("invalid");
    } else {
        confirmPassword.classList.add("invalid");
        confirmPassword.classList.remove("valid");
    }
});

// SUBMIT
document.querySelector(".register-form").addEventListener("submit", (e) => {

    if (password.value !== confirmPassword.value) {
        e.preventDefault();
        errorMessage.textContent = "Passwords do not match";
        errorMessage.classList.add("active");
    }
});

// 👁️ TOGGLE PASSWORD
document.querySelectorAll(".toggle-password").forEach(icon => {

    icon.addEventListener("click", () => {
        const inputId = icon.getAttribute("data-target");
        const input = document.getElementById(inputId);

        const isHidden = input.type === "password";

        // Cambiar tipo
        input.type = isHidden ? "text" : "password";

        // Cambiar icono
        icon.src = isHidden
            ? icon.getAttribute("data-closed")
            : icon.getAttribute("data-open");
    });

});