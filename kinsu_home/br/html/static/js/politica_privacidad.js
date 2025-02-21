import { fetchPageData } from '/static/js/fetch_page_data.js';

async function init() {
    var url = 'http://127.0.0.1:8055';

    const pageData = await fetchPageData(url, 'politica_privacidad' ,1); // Obtiene la página 1 dinámicamente
    if (pageData) {
        console.log('Content loaded:', pageData);
        window.pageData = pageData; // ✅ Guardamos en window para acceso global
        document.getElementById("title").innerText = window.pageData.title;
        document.getElementById("politica").innerHTML = window.pageData.politica;
        document.getElementById("footer").innerText = window.pageData.footer;
    } else {
        console.error('No se pudo cargar la página');
    }

}

init();
