FROM python:3.10-slim-buster

WORKDIR /app

# Copia el contenido de tu carpeta 'app' local (que incluye 'data', 'templates', 'static')
# al directorio de trabajo '/app' en el contenedor.
# Copia el requirements.txt que está en la raíz de tu repositorio
COPY requirements.txt .

# Copia el contenido de tu carpeta 'app' local (que incluye 'data', 'templates', 'static')
# al directorio de trabajo '/app' en el contenedor.
COPY app/ .

RUN pip install --no-cache-dir -r requirements.txt

# **NUEVA LÍNEA CLAVE**
ENV FLASK_APP=main.py

# Expón el puerto donde Flask se ejecutará
EXPOSE 5000

# Comando para iniciar la aplicación Flask
CMD ["flask", "run", "--host", "0.0.0.0"]