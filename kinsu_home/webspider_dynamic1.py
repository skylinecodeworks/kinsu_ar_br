#!/usr/bin/env python3

import os
import sys
from urllib.parse import urlparse, urljoin
from collections import deque

# Playwright
from playwright.sync_api import sync_playwright

def make_valid_filename(url_path):
    """
    Convierte una ruta de URL en un nombre de archivo válido.
    Si está vacía o es '/', devuelve 'index.html'.
    """
    if not url_path or url_path == '/':
        return "index.html"
    
    # Quitar la barra final si existe
    if url_path.endswith('/'):
        url_path = url_path[:-1]
    
    # Reemplazar caracteres que no sean válidos en Windows, etc.
    for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        url_path = url_path.replace(char, '_')
    
    # Si no tiene extensión, forzamos .html
    if '.' not in os.path.basename(url_path):
        url_path += '.html'
    
    return url_path

def get_local_path(url, base_folder):
    """
    Genera la ruta local donde se guardará el HTML correspondiente a `url`.
    Estructura: base_folder / dominio / [path transformado]
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # Carpetas base
    domain_folder = os.path.join(base_folder, domain)
    os.makedirs(domain_folder, exist_ok=True)
    
    # Nombre de archivo
    filename = make_valid_filename(path)
    local_path = os.path.join(domain_folder, filename)
    return local_path

def is_same_domain(url, root_domain):
    """
    Verifica si la URL pertenece al mismo dominio (hostname) que root_domain.
    """
    return urlparse(url).netloc == root_domain

def crawl_website(root_url, base_folder="descargas"):
    """
    Usa Playwright para navegar dinámicamente un sitio React (o similar) y 
    descargar el HTML renderizado de cada "ruta" alcanzable a través de enlaces.
    """
    # Normalizamos la URL raíz
    root_url = root_url.strip()
    if not root_url.startswith("http"):
        root_url = "http://" + root_url
    
    parsed_root = urlparse(root_url)
    root_domain = parsed_root.netloc
    
    # Creamos cola de URLs por visitar y un set de visitadas
    to_visit = deque([root_url])
    visited = set()
    
    # Abre Playwright y lanza el navegador
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        while to_visit:
            current_url = to_visit.popleft()
            
            # Si ya se visitó, saltamos
            if current_url in visited:
                continue
            
            visited.add(current_url)
            print(f"[INFO] Visitando: {current_url}")
            
            try:
                page.goto(current_url, timeout=15000)  # 15 segundos de timeout
                # Esperamos un poco a que React renderice:
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[ERROR] No se pudo navegar a {current_url} - {e}")
                continue
            
            # Guardar el HTML final
            html_content = page.content()
            local_path = get_local_path(current_url, base_folder)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"[INFO] Guardado HTML en {local_path}")
            
            # Opcional: Descarga de recursos estáticos.
            # En muchos casos, React maneja los recursos (JS, CSS) en rutas /static/ 
            # o similares. Para hacer un "mirroring" completo, habría que interceptar 
            # peticiones de red. Este ejemplo se enfoca en el HTML final.
            
            # Buscar enlaces en el DOM para seguir navegando
            # Obtenemos todos los <a href="...">
            anchor_elements = page.query_selector_all("a")
            for anchor in anchor_elements:
                href = anchor.get_attribute("href")
                if not href:
                    continue
                # Construimos la URL completa
                full_url = urljoin(current_url, href)
                # Solo añadimos si pertenece al mismo dominio
                if is_same_domain(full_url, root_domain):
                    # Evitar anclas (fragmentos)
                    parsed_link = urlparse(full_url)
                    cleaned_link = parsed_link._replace(fragment="").geturl()
                    
                    if cleaned_link not in visited and cleaned_link not in to_visit:
                        to_visit.append(cleaned_link)
        
        browser.close()

def main():
    if len(sys.argv) < 2:
        print("Uso: python webspider_dynamic.py <URL>")
        print("Ejemplo: python webspider_dynamic.py https://kinsu.mx/")
        sys.exit(1)
    
    root_url = sys.argv[1]
    
    base_folder = "descargas_react"  # Carpeta donde se guardará todo
    os.makedirs(base_folder, exist_ok=True)
    
    crawl_website(root_url, base_folder)
    print("[INFO] Rastreado finalizado.")

if __name__ == "__main__":
    main()

