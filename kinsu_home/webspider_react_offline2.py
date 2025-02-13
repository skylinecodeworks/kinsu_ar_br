#!/usr/bin/env python3
import os
import sys
import re
from urllib.parse import urlparse, urljoin
from collections import deque

from playwright.sync_api import sync_playwright

# -------------------------------------
# CONFIGURACIÓN / CONSTANTES
# -------------------------------------
BASE_FOLDER = "descarga_offline"  # Carpeta base donde se guardará todo

# Tipos de recurso que sí queremos interceptar y descargar (puedes ajustar)
INTERCEPT_RESOURCE_TYPES = ["image", "stylesheet", "script", "font", "xhr", "fetch"]


# -------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------
def make_valid_filename(path: str) -> str:
    """
    Convierte una ruta (o nombre de fichero) en algo válido para el sistema de archivos.
    Reemplaza caracteres problemáticos, etc.
    """
    invalid_chars_pattern = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars_pattern, "_", path)

def local_path_for_resource(url: str) -> str:
    """
    Dada la URL completa de un recurso estático (CSS, JS, imagen, fuente, etc.),
    genera la ruta LOCAL donde lo guardaremos.

    Ejemplo:
        url = https://example.com/static/css/main.abcdef.css
        ->  BASE_FOLDER/example.com/static/css/main.abcdef.css
    """
    parsed = urlparse(url)
    domain = parsed.netloc  # e.g. "example.com"
    path = parsed.path       # e.g. "/static/css/main.abcdef.css"

    # Asegurarnos de que el path no quede vacío. Si es "/" o "", forzamos algún nombre
    if not path or path == "/":
        path = "/index_resource"

    # Limpiamos caracteres conflictivos
    cleaned_path = make_valid_filename(path.lstrip("/"))  # quita barra inicial
    local_file_path = os.path.join(BASE_FOLDER, domain, cleaned_path)

    # Aseguramos que la carpeta existe
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    return local_file_path

def local_path_for_html(url: str) -> str:
    """
    Genera la ruta local donde guardaremos la página HTML.

    - Si la URL acaba en "/", o no tiene 'path', se asume "index.html".
    - Se almacenará en: BASE_FOLDER/<domain>/<path_sin_barra_final>.html
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path

    if not path or path.endswith("/"):
        path = (path or "/") + "index.html"

    cleaned_path = make_valid_filename(path.lstrip("/"))
    local_html_path = os.path.join(BASE_FOLDER, domain, cleaned_path)

    os.makedirs(os.path.dirname(local_html_path), exist_ok=True)
    return local_html_path

def is_same_domain(url: str, root_domain: str) -> bool:
    """
    Determina si la 'url' pertenece al mismo dominio que 'root_domain'.
    """
    return urlparse(url).netloc == root_domain


# -------------------------------------
# FUNCIÓN PRINCIPAL DE RASTREO
# -------------------------------------
def crawl_with_resources(root_url: str):
    """
    - Usa Playwright para navegar a 'root_url'.
    - Intercepta peticiones para descargar recursos estáticos en local.
    - Guarda el HTML renderizado, reescribiendo referencias a esos recursos.
    - Sigue enlaces <a> del mismo dominio.
    """
    # Normalizamos la URL raíz
    parsed_root = urlparse(root_url)
    root_domain = parsed_root.netloc

    # Estructuras de datos
    to_visit = deque([root_url])
    visited = set()

    # Diccionario para mapear "URL original" -> "ruta local" en el disco.
    # Así, luego podemos reescribir en el HTML.
    resource_map = {}

    # Iniciamos Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # -------------------------------------
        # FUNCIÓN DE INTERCEPCIÓN
        # -------------------------------------
        def handle_route(route):
            """
            Se llama cada vez que la página solicita un recurso.
            Decidimos si lo descargamos en local (si es un recurso estático)
            y cumplimos la petición con route.fulfill().
            """
            request = route.request
            url = request.url
            resource_type = request.resource_type

            # Si queremos interceptar y descargar este tipo de recurso...
            if resource_type in INTERCEPT_RESOURCE_TYPES:
                try:
                    # Descargamos el contenido (la respuesta) con route.fetch()
                    resp = route.fetch()
                    # Generamos la ruta local
                    local_file_path = local_path_for_resource(url)
                    resource_map[url] = local_file_path

                    # Guardamos en disco
                    with open(local_file_path, "wb") as f:
                        f.write(resp.body())

                    # Para servirlo offline "al vuelo" (sin descargarlo de la red),
                    # podríamos usar route.fulfill(...). Sin embargo, si no te importa
                    # que el navegador lo descargue de la red, se puede usar route.continue_().
                    # Aun así, para forzar la carga local, haremos fulfill:
                    route.fulfill(
                        status=resp.status,
                        headers=resp.headers,
                        body=resp.body()
                    )
                except Exception as ex:
                    print(f"[ERROR] Al descargar recurso {url}: {ex}")
                    # Si falla, dejamos que siga la petición normal
                    route.continue_()
            else:
                # No es un recurso que nos interese interceptar o
                # es el documento principal (resource_type == "document" o "other")
                route.continue_()

        # Activamos la intercepción para todas las peticiones:
        context.route("**/*", handle_route)
        page = context.new_page()

        # -------------------------------------
        # RASTREO
        # -------------------------------------
        while to_visit:
            current_url = to_visit.popleft()

            if current_url in visited:
                continue
            visited.add(current_url)

            print(f"[INFO] Visitando: {current_url}")

            # Navegamos
            try:
                page.goto(current_url, timeout=30000)  # 30 seg
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[ERROR] No se pudo navegar a {current_url} -> {e}")
                continue

            # Obtenemos el HTML final (renderizado)
            html_content = page.content()

            # Reemplazamos en el HTML todas las referencias
            # a URLs originales por la ruta local en disco.
            #
            # Esto es un string replace naive. Para algo más sólido,
            # podría hacerse un parse con BeautifulSoup y cambiar solo
            # en atributos src, href, etc.
            for original_url, local_path in resource_map.items():
                # Normalizamos las barras (Windows, etc.)
                local_path_norm = local_path.replace("\\", "/")
                # Reemplazo directo
                html_content = html_content.replace(original_url, local_path_norm)

            # Guardamos la página HTML con las rutas reescritas
            local_html_path = local_path_for_html(current_url)
            with open(local_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[INFO] HTML guardado en: {local_html_path}")

            # Buscamos enlaces <a> en el DOM para seguir rastreando
            anchors = page.query_selector_all("a")
            for a in anchors:
                href = a.get_attribute("href")
                if not href:
                    continue

                # Construimos URL absoluta
                full = urljoin(current_url, href)

                # Quitamos fragmentos (#anchor)
                parsed_link = urlparse(full)
                full_no_frag = parsed_link._replace(fragment="").geturl()

                # Solo si pertenece al mismo dominio
                if is_same_domain(full_no_frag, root_domain):
                    if full_no_frag not in visited and full_no_frag not in to_visit:
                        to_visit.append(full_no_frag)

        browser.close()  # Cerrar el navegador


# -------------------------------------
# MAIN
# -------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Uso: python webspider_react_offline.py <URL>")
        sys.exit(1)

    root_url = sys.argv[1].strip()
    if not root_url.startswith("http"):
        root_url = "https://" + root_url  # Ajuste si no lleva protocolo

    # Creamos la carpeta base si no existe
    os.makedirs(BASE_FOLDER, exist_ok=True)

    # Ejecutamos la lógica de rastreo
    crawl_with_resources(root_url)
    print("[INFO] Proceso finalizado.")


if __name__ == "__main__":
    main()

