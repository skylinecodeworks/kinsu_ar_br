export async function fetchSiteMap(id) {
    try {
        const response = await fetch('http://127.0.0.1:8055/items/site_map');
        if (!response.ok) {
            throw new Error(`Error en la solicitud: ${response.statusText}`);
        }
        const jsonResponse = await response.json();

        // Buscar el objeto con el ID especificado en el array "data"
        const item = jsonResponse.data.find(entry => entry.id === id);
        if (!item) {
            throw new Error(`No se encontró el sitio con ID: ${id}`);
        }

        // Parsear la propiedad "tree"
        return JSON.parse(item.tree);
    } catch (error) {
        console.error('Error obteniendo el mapa del sitio:', error);
        return null;
    }
}

// Pre-cargar el mapa del sitio antes de que la web inicie
export let siteMapData = null;

export async function preloadSiteMap(id) {
    siteMapData = await fetchSiteMap(id);
    return siteMapData;
}
