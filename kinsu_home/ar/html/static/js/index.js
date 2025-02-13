import { preloadSiteMap, siteMapData } from '/static/js/sitemap.js';
import { fetchPageData } from '/static/js/fetch_page_data.js';

async function init() {
    await preloadSiteMap(1); // Carga el mapa del sitio

    const pageData = await fetchPageData(1); // Obtiene la página 1 dinámicamente
    if (pageData) {
        console.log('Content loaded:', pageData);
        window.pageData = pageData; // ✅ Guardamos en window para acceso global
    } else {
        console.error('No se pudo cargar la página');
    }

    document.dispatchEvent(new Event('siteMapLoaded'));
}

init();
