FROM python:3.9-slim

WORKDIR /app

# Copiar el fichero de requerimientos y el fichero .env
COPY requirements.txt ./
COPY .env ./

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto 80 y arrancar la aplicación con Uvicorn
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

