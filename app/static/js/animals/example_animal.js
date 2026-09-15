// Demostración: no guarda datos ni realiza peticiones al servidor.

const root = document.getElementById("example-animal");

if (root) {
    const form = root.querySelector("#example-animal-form");
    const fields = root.querySelector("#example-fields");
    const selector = root.querySelector("#animal-type");

    const status = root.querySelector("#example-status");
    const description = root.querySelector("#preview-description");

    // Datos enviados por Flask e incluidos en el template con tojson.
    const examples = JSON.parse(
        document.getElementById("example-animals-data").textContent
    );

    const editable = [
        "identification",
        "name",
        "breed",
        "sex",
        "birth_date",
        "weight",
        "observations"
    ];

    // Obtener un campo del formulario.
    const control = (name) => form.elements.namedItem(name);

    // Actualizar texto sin interpretar HTML ingresado por el usuario.
    const setText = (name, value) => {
        root.querySelector(`#preview-${name}`).textContent = value;
    };

    // Impedir fechas de nacimiento futuras usando la fecha local.
    const today = new Date();

    control("birth_date").max = [
        today.getFullYear(),
        String(today.getMonth() + 1).padStart(2, "0"),
        String(today.getDate()).padStart(2, "0")
    ].join("-");

    // ─────────────────────────────────────────────
    // Actualizar la ficha con los datos del formulario
    // ─────────────────────────────────────────────
    function renderPreview() {
        const values = Object.fromEntries(
            editable.map((key) => [
                key,
                control(key).value.trim()
            ])
        );

        const isGoat = selector.value === "cabra";

        setText("identification", values.identification);
        setText("name", values.name || "Unnamed animal");

        setText("species", isGoat ? "Goat" : "Sheep");
        setText("icon", isGoat ? "🐐" : "🐑");

        setText("breed", values.breed || "Not provided");

        setText(
            "sex",
            values.sex === "Hembra" ? "Female" : "Male"
        );

        setText(
            "birth_date",
            values.birth_date || "Not provided"
        );

        setText(
            "weight",
            values.weight
                ? `${Number(values.weight)} kg`
                : "Not provided"
        );

        setText(
            "observations",
            values.observations || "No observations added."
        );
    }

    // ─────────────────────────────────────────────
    // Cargar o restablecer el ejemplo seleccionado
    // ─────────────────────────────────────────────
    function loadExample() {
        const sample = examples[selector.value];

        for (const key of editable) {
            control(key).value = sample[key] ?? "";
            control(key).setCustomValidity("");
        }

        control("species").value =
            selector.value === "cabra" ? "Goat" : "Sheep";

        renderPreview();

        description.textContent =
            "This is how an individual record could look.";

        status.textContent =
            "Sample record loaded. Nothing has been saved.";
    }

    // ─────────────────────────────────────────────
    // Avisar cuando hay cambios pendientes de visualizar
    // ─────────────────────────────────────────────
    form.addEventListener("input", (event) => {
        if (event.target === selector) return;

        control("identification").setCustomValidity("");

        description.textContent =
            "Click Preview animal record to apply your changes.";

        status.textContent =
            "You have changes that are not reflected in this preview.";
    });

    // ─────────────────────────────────────────────
    // Validar y mostrar la ficha sin enviar el formulario
    // ─────────────────────────────────────────────
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const identification = control("identification");

        identification.setCustomValidity(
            identification.value.trim()
                ? ""
                : "Enter an animal identification."
        );

        if (!form.reportValidity()) return;

        renderPreview();

        description.textContent =
            "Preview updated with your example details.";

        status.textContent =
            "Example preview complete. No animal has been registered or saved.";

        root.querySelector("#record-title").focus();
    });

    // Cambiar entre oveja y cabra.
    selector.addEventListener("change", loadExample);

    // Restablecer los datos del animal seleccionado.
    root.querySelector("#reset-example").addEventListener(
        "click",
        loadExample
    );

    // Habilitar el formulario una vez instalados los eventos.
    fields.disabled = false;
}