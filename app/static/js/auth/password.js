document.addEventListener("DOMContentLoaded", () => {

    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");

    const rulesBox = document.getElementById("password-rules");
    const strengthBar = document.querySelector(".strength-bar");

    const ruleLength = document.getElementById("rule-length");
    const ruleUpper = document.getElementById("rule-uppercase");
    const ruleNumber = document.getElementById("rule-number");
    const ruleSpecial = document.getElementById("rule-special");

    // 🔐 SHOW RULES
    if (password && rulesBox) {
        password.addEventListener("focus", () => {
            rulesBox.classList.add("active");
        });

    document.addEventListener("click", (e) => {

        if (!rulesBox) return;

        const clickedInsidePassword =
            e.target.closest(".password-wrapper") ||
            e.target.closest(".password-rules");

        if (!clickedInsidePassword) {
            rulesBox.classList.remove("active");
        }

    });
    
    }

    // 🔐 PASSWORD RULES + STRENGTH
    if (password) {
        password.addEventListener("input", () => {

            // 🔥 MOSTRAR RULES SI HAY TEXTO
            if (password.value.length > 0) {
                rulesBox.classList.add("active");
            } else {
                rulesBox.classList.remove("active");
            }

            const value = password.value;
            let strength = 0;

            const checks = [
                { test: value.length >= 6, el: ruleLength },
                { test: /[A-Z]/.test(value), el: ruleUpper },
                { test: /[0-9]/.test(value), el: ruleNumber },
                { test: /[^A-Za-z0-9]/.test(value), el: ruleSpecial }
            ];

            checks.forEach(rule => {
                if (!rule.el) return;

                rule.el.classList.toggle("valid", rule.test);
                rule.el.classList.toggle("invalid", !rule.test);

                if (rule.test) strength += 25;
            });

            if (strengthBar) {
                strengthBar.style.width = strength + "%";

                if (strength < 50) strengthBar.style.background = "red";
                else if (strength < 75) strengthBar.style.background = "orange";
                else strengthBar.style.background = "green";
            }

        });
    }

    // 🔁 CONFIRM PASSWORD
    if (confirmPassword && password) {
        confirmPassword.addEventListener("input", () => {

            const match =
                confirmPassword.value === password.value &&
                confirmPassword.value !== "";

            confirmPassword.classList.toggle("valid", match);
            confirmPassword.classList.toggle("invalid", !match);
        });
    }

    // 👁️ TOGGLE PASSWORD
    document.querySelectorAll(".toggle-password").forEach(icon => {

        icon.addEventListener("click", () => {

            const targetId = icon.dataset.target;
            const input = document.getElementById(targetId);

            if (!input) return;

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

});