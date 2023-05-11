# Selecciona la imagen base de Python, en este caso la versión 3.8
FROM python:3.10-slim-buster

ENV PUID=1000
ENV PGID=1000
ENV LOG_LEVEL=DEBUG
ENV OUTPUT_DIR=/output

# Instala pipenv
RUN pip install pipenv

# Establece el directorio de trabajo para la aplicación
WORKDIR /app

# Copia el archivo Pipfile y Pipfile.lock a la imagen
COPY Pipfile* ./

# Instala las dependencias del proyecto utilizando pipenv
RUN pipenv install --system --deploy

# Copia todos los archivos del proyecto al directorio de trabajo de la imagen
COPY . .

RUN groupadd -g $PGID pythongroup && useradd -u $PUID -g $PGID -m pythonuser
RUN mkdir $OUTPUT_DIR && chown $PGID:$PGID $OUTPUT_DIR

USER pythonuser

ENTRYPOINT ["python", "app.py"]