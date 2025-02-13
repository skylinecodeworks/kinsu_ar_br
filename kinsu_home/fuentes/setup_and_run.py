import os
import sys
import subprocess

VENV_NAME = "venv_fuentes"
PYTHON_CMD = sys.executable  # Obtiene la ruta del ejecutable de Python actual

def verificar_instalacion_uv():
    """Verifica si `uv` está instalado y lo instala si no está disponible"""
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
        print("✅ `uv` ya está instalado.")
    except subprocess.CalledProcessError:
        print("❌ `uv` no está instalado. Instálalo manualmente con:")
        print("   pip install uv")
        sys.exit(1)

def crear_entorno_virtual():
    """Crea un entorno virtual con `uv`"""
    if not os.path.exists(VENV_NAME):
        print(f"🌱 Creando entorno virtual '{VENV_NAME}' con `uv`...")
        subprocess.run(["uv", "venv", VENV_NAME], check=True)
        print("✅ Entorno virtual creado con éxito.")
    else:
        print(f"🔄 El entorno virtual '{VENV_NAME}' ya existe.")

def instalar_dependencias():
    """Instala las dependencias necesarias en el entorno virtual"""
    pip_path = os.path.join(VENV_NAME, "bin" if os.name != "nt" else "Scripts", "pip")
    print("📦 Instalando dependencias con `uv`...")
    subprocess.run([pip_path, "install", "requests", "beautifulsoup4"], check=True)
    print("✅ Dependencias instaladas correctamente.")

def ejecutar_script():
    """Ejecuta el script de descarga de fuentes"""
    python_path = os.path.join(VENV_NAME, "bin" if os.name != "nt" else "Scripts", "python")
    script_code = """
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

url = "https://kinsu.mx"
output_folder = "fuentes_descargadas"
os.makedirs(output_folder, exist_ok=True)

def obtener_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None

def extraer_fuentes_de_css(css_content, base_url):
    fuentes = set()
    for line in css_content.splitlines():
        if "url(" in line and any(ext in line for ext in [".woff", ".woff2", ".ttf", ".otf"]):
            try:
                font_url = line.split("url(")[1].split(")")[0].strip("'\\\"")
                font_url = urljoin(base_url, font_url)
                fuentes.add(font_url)
            except IndexError:
                continue
    return fuentes

html_content = obtener_html(url)
if not html_content:
    exit()

soup = BeautifulSoup(html_content, "html.parser")
font_urls = set()

for link in soup.find_all("link", href=True):
    href = link["href"]
    if href.endswith(".css"):
        css_url = urljoin(url, href)
        css_content = obtener_html(css_url)
        if css_content:
            font_urls.update(extraer_fuentes_de_css(css_content, css_url))

for style in soup.find_all("style"):
    if style.string:
        font_urls.update(extraer_fuentes_de_css(style.string, url))

for font_url in font_urls:
    try:
        font_response = requests.get(font_url, timeout=10)
        font_response.raise_for_status()
        font_name = os.path.basename(urlparse(font_url).path)
        font_path = os.path.join(output_folder, font_name)

        with open(font_path, "wb") as font_file:
            font_file.write(font_response.content)

        print(f"✅ Descargada: {font_name}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar {font_url}: {e}")

print("🎉 Proceso completado.")
    """
    
    # Guarda el script en el entorno virtual antes de ejecutarlo
    script_path = os.path.join(VENV_NAME, "script_fuentes.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_code)
    
    print("🚀 Ejecutando el script de descarga de fuentes...")
    subprocess.run([python_path, script_path], check=True)

def main():
    verificar_instalacion_uv()
    crear_entorno_virtual()
    instalar_dependencias()
    ejecutar_script()

if __name__ == "__main__":
    main()

