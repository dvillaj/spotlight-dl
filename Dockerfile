# Selecciona la imagen base de Python, en este caso la versión 3.8
FROM python:3.10-slim-buster

ENV PUID=1033
ENV PGID=100
ENV OUTPUT_DIR=/images
ENV TZ=Europe/Madrid

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

RUN groupadd -g $PGID pythongroup || true && \
    useradd -u $PUID -g $PGID -m pythonuser && \
    mkdir $OUTPUT_DIR && chown $PUID:$PGID $OUTPUT_DIR && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

USER pythonuser

ENTRYPOINT ["python", "app.py"]
