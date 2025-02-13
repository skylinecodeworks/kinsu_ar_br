export async function fetchPageData(pageNumber) {
    try {
        const response = await fetch(`http://127.0.0.1:8055/items/Paginas/${pageNumber}`);
        if (!response.ok) {
            throw new Error(`Error al obtener la página ${pageNumber}: ${response.statusText}`);
        }
        const data = await response.json();
        return data.data; // Retorna solo la parte útil de la respuesta
    } catch (error) {
        console.error('Error al obtener datos de la página:', error);
        return null;
    }
}