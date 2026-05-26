const email = document.getElementById("email");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm-password");
const terms = document.getElementById("terms");

const strengthBar = document.querySelector(".strength-bar");

// reglas visuales
const rulesBox = document.getElementById("password-rules");
const ruleLength = document.getElementById("rule-length");
const ruleUpper = document.getElementById("rule-uppercase");
const ruleNumber = document.getElementById("rule-number");
const ruleSpecial = document.getElementById("rule-special");


// =========================
// 📧 EMAIL VALIDATION
// =========================
email.addEventListener("input", () => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (regex.test(email.value)) {
        email.classList.add("valid");
        email.classList.remove("invalid");
    } else {
        email.classList.add("invalid");
        email.classList.remove("valid");
    }
});


// =========================
// 🔐 PASSWORD RULES PANEL
// =========================

// Mostrar reglas
password.addEventListener("focus", () => {
    rulesBox.classList.add("active");
});

// Ocultar reglas (opcional)
password.addEventListener("blur", () => {
    rulesBox.classList.remove("active");
});


// =========================
// 🔐 PASSWORD STRENGTH + RULES
// =========================
password.addEventListener("input", () => {
    const value = password.value;
    let strength = 0;

    // Length
    if (value.length >= 6) {
        strength += 25;
        ruleLength.classList.add("valid");
        ruleLength.classList.remove("invalid");
    } else {
        ruleLength.classList.add("invalid");
        ruleLength.classList.remove("valid");
    }

    // Uppercase
    if (/[A-Z]/.test(value)) {
        strength += 25;
        ruleUpper.classList.add("valid");
        ruleUpper.classList.remove("invalid");
    } else {
        ruleUpper.classList.add("invalid");
        ruleUpper.classList.remove("valid");
    }

    // Number
    if (/[0-9]/.test(value)) {
        strength += 25;
        ruleNumber.classList.add("valid");
        ruleNumber.classList.remove("invalid");
    } else {
        ruleNumber.classList.add("invalid");
        ruleNumber.classList.remove("valid");
    }

    // Special char
    if (/[^A-Za-z0-9]/.test(value)) {
        strength += 25;
        ruleSpecial.classList.add("valid");
        ruleSpecial.classList.remove("invalid");
    } else {
        ruleSpecial.classList.add("invalid");
        ruleSpecial.classList.remove("valid");
    }

    // Barra visual
    strengthBar.style.width = strength + "%";

    if (strength < 50) {
        strengthBar.style.background = "red";
    } else if (strength < 75) {
        strengthBar.style.background = "orange";
    } else {
        strengthBar.style.background = "green";
    }
});


// =========================
// 🔁 CONFIRM PASSWORD
// =========================
confirmPassword.addEventListener("input", () => {
    if (
        confirmPassword.value === password.value &&
        confirmPassword.value !== ""
    ) {
        confirmPassword.classList.add("valid");
        confirmPassword.classList.remove("invalid");
    } else {
        confirmPassword.classList.add("invalid");
        confirmPassword.classList.remove("valid");
    }
});


// =========================
// 🚀 FORM SUBMIT VALIDATION
// =========================
document.querySelector(".register-form").addEventListener("submit", (e) => {

    if (
        !email.classList.contains("valid") ||
        !confirmPassword.classList.contains("valid") ||
        !terms.checked
    ) {
        e.preventDefault();
        alert("Please complete the form correctly.");
    }
});

document.querySelectorAll(".toggle-password").forEach(icon => {

    icon.addEventListener("click", () => {

        const targetId = icon.dataset.target;
        const input = document.getElementById(targetId);

        const isHidden = icon.dataset.state === "hidden";

        if (isHidden) {
            input.type = "text";
            icon.src = icon.dataset.closed;
            icon.dataset.state = "visible";
        } else {
            input.type = "password";
            icon.src = icon.dataset.open;
            icon.dataset.state = "hidden";
        }

    });

});