import logging
import threading
from bottle import Bottle, template, TEMPLATE_PATH, request
from utils import *

app = Bottle()
TEMPLATE_PATH.append('./templates')


@app.route('/')
def index():
    images = read_images_database()
    nmax = min(10, len(images))

    return template_and_searchterms("Last downloaded images", images, images[:nmax])


# Ruta para la búsqueda
@app.route('/search')
def search():
    search_term = request.query.get('search-term')
    text = f"Results for '{search_term}'"

    images = read_images_database()
    image_list = [item for item in images if search_term.lower() in item['title'].lower()]

    return template_and_searchterms(text, images, image_list[:10])


def template_and_searchterms(text, images, image_list):
    search_terms = get_links()
    return template('index.html', counter=len(images), text=text, imagelist=image_list, search_terms=search_terms)


@app.route('/random')
def index():
    from random import sample

    images = read_images_database()
    nmax = min(10, len(images))

    return template_and_searchterms("Some random images", images, sample(images, nmax))

@app.route('/upload')
def index():
    return template('upload.html')


@app.route('/download')
def index():
    return template('download.html')


@app.route('/downloadImages')
def download():
    from bottle import static_file, response
    import os
    import tempfile
    import time

    config = AppConfig()
    tmp_dir = tempfile.mkdtemp()

    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"images-{timestamp}.zip"
    filepath = f'{tmp_dir}/{filename}'

    compress_directory(config.get_output_dir(), filepath)

    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return static_file(filename, root=os.path.dirname(filepath), download=filename)


@app.route('/uploadFile', method='POST')
def upload():
    from bottle import request
    import os
    import tempfile

    logger = logging.getLogger("uploadFile")
    upload = request.files.get('filename')
    filename = upload.filename
    if '.zip' in filename:
        tmp_dir = tempfile.mkdtemp()
        logger.debug(f"Temp path: {tmp_dir}")
        file_path = os.path.join(tmp_dir, filename)
        upload.save(file_path)

        decompress_zipfile(file_path, tmp_dir)
        inserted = insert_images_from_backup(tmp_dir)

        delete_directory(tmp_dir)

        return f'File {filename} has been processed successfully with {inserted} images inserted'
    else:
        return 'The upload file is not a zip file!'


def run_server():
    app.run(host='0.0.0.0', port=8001)


if __name__ == '__main__':
    conf_logging()
    logger = logging.getLogger("app")

    logger.info("Starting ...")

    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    logger.info(f"Web Server started in thread {server_thread.name} ...")

    setup_output_dir()
    initial_sleep()

    n = 1
    images = count_images_database()

    while True:
        logger.info(f"Iteration {n} - Images {images} ...")
        for item in get_images_data():
            if process_image(item):
                images = images + 1

        sleep()
        n = n + 1