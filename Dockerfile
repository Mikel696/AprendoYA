FROM python:3.10-slim-buster

WORKDIR /app # Este será el directorio de trabajo, es decir, el root del proyecto dentro del contenedor

# Copia todo el contenido de tu carpeta 'app' local al directorio de trabajo '/app' en el contenedor
COPY app/ .

# Copia el requirements.txt que está en la raíz de tu repo
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Si tienes la carpeta 'data' y 'templates' dentro de 'app', la línea de arriba debería ser suficiente
# para que se copien, ya que 'COPY app/ .' copia todo el contenido de 'app/'.

# Expón el puerto si es necesario, aunque Render lo hace automáticamente
EXPOSE 5000 # Flask por defecto usa 5000

# Comando para iniciar la aplicación Flask
CMD ["flask", "run", "--host", "0.0.0.0"]