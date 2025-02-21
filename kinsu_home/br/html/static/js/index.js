import { fetchPageData } from '/static/js/fetch_page_data.js';

async function init() {
    var url = 'http://44.194.95.25:8055';

    const pageData = await fetchPageData(url, 'landing' ,1); // Obtiene la página 1 dinámicamente
    if (pageData) {
        console.log('Content loaded:', pageData);
        window.pageData = pageData; // ✅ Guardamos en window para acceso global

        document.getElementById("title").innerText = window.pageData.title;
        document.getElementById("link_google_play").href = window.pageData.link_google_play;
        document.getElementById("link_app_store").href = window.pageData.link_app_store;

        document.getElementById("title2").innerText = window.pageData.title2;
        document.getElementById("subtitle2").innerText = window.pageData.subtitle2;
        document.getElementById("image2").src = url + '/assets/' + window.pageData.image2;

        document.getElementById("title3").innerText = window.pageData.title3;
        document.getElementById("subtitle3").innerText = window.pageData.subtitle3;
        document.getElementById("image3").src = url + '/assets/' + window.pageData.image3;

        document.getElementById("title4").innerText = window.pageData.title4;
        document.getElementById("subtitle4").innerText = window.pageData.subtitle4;
        document.getElementById("image4").src = url + '/assets/' + window.pageData.image4;

        document.getElementById("chat_text").innerText = window.pageData.chat_text;
        document.getElementById("chat1_text").href = window.pageData.chat1_text;
        document.getElementById("chat1_image").src = url + '/assets/' + window.pageData.chat1_image;
        document.getElementById("chat2_text").href = window.pageData.chat2_text;
        document.getElementById("chat2_image").src = url + '/assets/' + window.pageData.chat2_image;
        document.getElementById("chat3_text").href = window.pageData.chat3_text;
        document.getElementById("chat3_image").src = url + '/assets/' + window.pageData.chat3_image;

        document.getElementById("footer").innerText = window.pageData.footer;
    } else {
        console.error('No se pudo cargar la página');
    }

    // Agregar evento para el botón de registro
    setupRegistrationForm(url);
}

// Función para mostrar mensajes en el formulario
function showMessage(message, isSuccess = false) {
    const messageElement = document.getElementById("form_message");
    if (messageElement) {
        messageElement.innerText = message;
        messageElement.style.color = isSuccess ? "green" : "red";
    }
}

// Función para validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Función para validar teléfono (solo números y mínimo 7 caracteres)
function isValidPhone(phone) {
    const phoneRegex = /^[0-9]{7,}$/;
    return phoneRegex.test(phone);
}

// Función para validar contraseña segura
function isValidPassword(password) {
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
}

// Función para manejar el registro de usuarios
function setupRegistrationForm(url) {
    const registrationButton = document.getElementById("registration_button");
    if (!registrationButton) {
        console.error("Botón de registro no encontrado");
        return;
    }

    registrationButton.addEventListener("click", async function () {
        const inputs = document.querySelectorAll(".form-container input");
        const name = inputs[0].value.trim();
        const email = inputs[1].value.trim();
        const phone = inputs[2].value.trim();
        const password = inputs[3].value.trim();

        // Validaciones
        if (!name || !email || !phone || !password) {
            showMessage("Todos os campos são obrigatórios.");
            return;
        }

        if (!isValidEmail(email)) {
            showMessage("O e-mail não é válido.");
            return;
        }

        if (!isValidPhone(phone)) {
            showMessage("O número de telefone deve conter apenas números e ter pelo menos 7 dígitos.");
            return;
        }

        if (!isValidPassword(password)) {
            showMessage("A senha deve ter pelo menos 8 caracteres, incluir um número e um caractere especial.");
            return;
        }

        const data = { name, email, phone, password };

        try {
            const response = await fetch(`${url}/items/registration`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const result = await response;

            if (result.status == '204') {
                showMessage("Registro realizado com sucesso. Bem-vindo!", true);
            } else {

                showMessage("O registro não é possível.");

            }
        } catch (error) {
            console.error("Error en la solicitud:", error);
            showMessage("Ocorreu um erro durante o registro.");
        }
    });
}

init();
