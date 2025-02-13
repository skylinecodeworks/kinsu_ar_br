#!/usr/bin/env python3
import os
import sys
import re
from urllib.parse import urlparse, urljoin
from collections import deque

from playwright.sync_api import sync_playwright

# ----------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------

BASE_FOLDER = "descarga_offline"

# Tipos de recurso que queremos interceptar y descargar.
# (Puedes añadir "xhr", "fetch" si necesitas esos también.)
INTERCEPT_RESOURCE_TYPES = ["image", "stylesheet", "script", "font"]

# Para clasificar y ubicar en subcarpetas de "static/"
# según extensión o resource_type.
EXTENSION_MAP = {
    "css":  "css",
    "js":   "js",
    "png":  "media",
    "jpg":  "media",
    "jpeg": "media",
    "gif":  "media",
    "svg":  "media",
    "ico":  "media",
    "woff": "media",
    "woff2":"media",
    "ttf":  "media",
    # etc...
}


# ----------------------------------------------------------------
# FUNCIONES AUXILIARES
# ----------------------------------------------------------------

def make_valid_filename(path: str) -> str:
    """
    Reemplaza caracteres conflictivos para el sistema de archivos.
    """
    invalid_chars_pattern = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars_pattern, "_", path)

def pick_subfolder(url: str, resource_type: str) -> str:
    """
    Determina la subcarpeta 'static/js', 'static/css', 'static/media' 
    según la extensión o el tipo de recurso.
    Si no coincide con nada, retorna 'static/other'.
    """
    parsed = urlparse(url)
    # Obtener la extensión sin el "."
    _, dot, ext = parsed.path.rpartition(".")  # 'logo' '.' 'png'
    ext = ext.lower()

    if resource_type == "stylesheet" or ext == "css":
        return "static/css"
    elif resource_type == "script" or ext == "js":
        return "static/js"
    elif resource_type in ("image", "font") or ext in EXTENSION_MAP:
        folder = EXTENSION_MAP.get(ext, "media")
        return f"static/{folder}"
    else:
        return "static/other"

def local_path_for_html(root_domain: str, url: str) -> str:
    """
    Genera la ruta local donde se guardará el HTML, 
    reflejando la estructura de la URL en directorios.

    Si la URL es:
        https://kinsu.mx/  ->  descarga_offline/kinsu.mx/index.html
        https://kinsu.mx/about -> descarga_offline/kinsu.mx/about.html
        https://kinsu.mx/faq/  -> descarga_offline/kinsu.mx/faq/index.html
        https://kinsu.mx/blog/post?x=1 -> blog/post.html (params omitidos)
    """
    parsed = urlparse(url)
    path = parsed.path
    if not path or path == "/":
        path = "/index.html"
    elif path.endswith("/"):
        path = path + "index.html"

    # Quitar parámetros (ej: ?id=123)
    # Lo más sencillo: 
    #    -> si hay ".", asumimos extensión
    #    -> si no, le ponemos .html
    # Pero en sitios SPA puede haber rutas sin extensión, p.ej. /about
    filename = os.path.basename(path)
    dir_name = os.path.dirname(path)

    # Limpieza de caracteres conflictivos
    filename = make_valid_filename(filename)
    dir_name = make_valid_filename(dir_name.lstrip("/"))

    # Construimos la ruta final
    base_dir = os.path.join(BASE_FOLDER, root_domain, dir_name)
    os.makedirs(base_dir, exist_ok=True)

    local_html_path = os.path.join(base_dir, filename)
    return local_html_path

def local_path_for_resource(root_domain: str, url: str, resource_type: str) -> str:
    """
    Genera una ruta local en subcarpetas:
      descarga_offline/<domain>/static/js/... (o css/media/etc.)

    - Determina subcarpeta en función de la extensión o resource_type
    - Asegura que la carpeta exista
    - Devuelve la ruta absoluta

    Ejemplo:
      https://kinsu.mx/static/js/main.abc.js 
      -> descarga_offline/kinsu.mx/static/js/main_abc.js
    """
    subfolder = pick_subfolder(url, resource_type)  # p.ej. "static/js"
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "resource"
    filename = make_valid_filename(filename)
    
    base_dir = os.path.join(BASE_FOLDER, root_domain, subfolder)
    os.makedirs(base_dir, exist_ok=True)

    local_file_path = os.path.join(base_dir, filename)
    return local_file_path

def relative_path_for_resource(html_path: str, resource_path: str) -> str:
    """
    Dada la ruta ABSOLUTA de un HTML y la ruta ABSOLUTA de un recurso,
    calcula la ruta RELATIVA desde el HTML al recurso.
    Ejemplo:
      - html_path = /.../kinsu.mx/faq/index.html
      - resource_path = /.../kinsu.mx/static/js/main_abc.js
      -> "../../static/js/main_abc.js"
    """
    html_dir = os.path.dirname(html_path)
    rel = os.path.relpath(resource_path, start=html_dir)
    return rel.replace("\\", "/")  # Normalizar barras en Windows

def is_same_domain(url: str, root_domain: str) -> bool:
    return urlparse(url).netloc == root_domain


# ----------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ----------------------------------------------------------------
def crawl_with_resources(root_url: str):
    """
    - Abre un navegador headless con Playwright.
    - Intercepta y descarga recursos estáticos en carpetas 'static/js', 'static/css', etc.
    - Guarda el HTML con rutas relativas para cada página visitada.
    - Sigue enlaces <a> del mismo dominio recursivamente.
    """
    parsed_root = urlparse(root_url)
    root_domain = parsed_root.netloc

    to_visit = deque([root_url])
    visited = set()

    # Diccionario para mapear "URL original" -> "ruta absoluta en disco" (del recurso).
    resource_map = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # ----------------------------------------------------
        # INTERCEPCIÓN DE PETICIONES
        # ----------------------------------------------------
        def handle_route(route):
            request = route.request
            url = request.url
            resource_type = request.resource_type

            # Interceptar solo los tipos que nos interesan (CSS, JS, imágenes, fuentes...)
            if resource_type in INTERCEPT_RESOURCE_TYPES:
                try:
                    resp = route.fetch()  # Descarga de la red
                    local_file_path = local_path_for_resource(root_domain, url, resource_type)
                    resource_map[url] = local_file_path

                    # Guardar en disco
                    with open(local_file_path, "wb") as f:
                        f.write(resp.body())

                    # Devolvemos la respuesta al navegador desde el contenido descargado
                    route.fulfill(
                        status=resp.status,
                        headers=resp.headers,
                        body=resp.body()
                    )
                except Exception as ex:
                    print(f"[ERROR] Al descargar recurso {url}: {ex}")
                    route.continue_()
            else:
                # Documentos, o tipos que no queremos interceptar
                route.continue_()

        context.route("**/*", handle_route)
        page = context.new_page()

        # ----------------------------------------------------
        # RASTREO
        # ----------------------------------------------------
        while to_visit:
            current_url = to_visit.popleft()
            if current_url in visited:
                continue
            visited.add(current_url)

            print(f"[INFO] Visitando: {current_url}")
            try:
                page.goto(current_url, timeout=30000)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[ERROR] No se pudo navegar a {current_url} -> {e}")
                continue

            # HTML final tras render
            html_content = page.content()

            # Guardar HTML en disco
            html_local_path = local_path_for_html(root_domain, current_url)

            # Reescribir referencias a recursos en el HTML
            # (cada URL "original_url" se reemplaza por la ruta relativa local).
            for original_url, absolute_resource_path in resource_map.items():
                # Calculamos la ruta relativa desde este HTML al recurso
                rel_path = relative_path_for_resource(html_local_path, absolute_resource_path)

                # Reemplazamos (naive) todas las apariciones de la URL original en el HTML
                # con esa ruta relativa.
                #
                # Un enfoque más robusto sería parsear con BeautifulSoup y modificar sólo
                # atributos <img src>, <link href>, <script src>, etc.
                html_content = html_content.replace(original_url, rel_path)

            # Guardamos el HTML ya modificado
            with open(html_local_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[INFO] HTML guardado en {html_local_path}")

            # Descubrir más enlaces <a> en la página
            anchors = page.query_selector_all("a")
            for a in anchors:
                href = a.get_attribute("href")
                if not href:
                    continue
                full_url = urljoin(current_url, href)
                parsed_link = urlparse(full_url)
                # Omitir el fragment
                link_no_frag = parsed_link._replace(fragment="").geturl()

                # Solo si es mismo dominio
                if is_same_domain(link_no_frag, root_domain):
                    if link_no_frag not in visited and link_no_frag not in to_visit:
                        to_visit.append(link_no_frag)

        browser.close()


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Uso: python webspider_react_offline.py <URL>")
        sys.exit(1)

    root_url = sys.argv[1].strip()
    if not root_url.startswith("http"):
        root_url = "https://" + root_url

    os.makedirs(BASE_FOLDER, exist_ok=True)

    crawl_with_resources(root_url)
    print("[INFO] Proceso finalizado.")


if __name__ == "__main__":
    main()

