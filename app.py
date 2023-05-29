import logging
import threading

from bottle import Bottle, template, TEMPLATE_PATH, request
from utils import *

app = Bottle()
TEMPLATE_PATH.append('./templates')


@app.route('/')
def index():
    images = read_images_database()
    nmax = min(AppConfig.get_images_per_page(), len(images))

    return template_and_search_terms("Latest downloaded images", images[:nmax])


@app.route('/search')
def search():

    search_term = request.query.get('search-term').encode('latin1').decode('utf-8').strip()

    image_list = search_term_database(search_term)
    text = f"{len(image_list)} images found with '{search_term}' term"

    return template_and_search_terms(text, image_list[:AppConfig.get_images_per_page()])


@app.route('/random')
def index():
    from random import sample

    images = read_images_database()
    nmax = min(AppConfig.get_images_per_page(), len(images))

    return template_and_search_terms("Some random images", sample(images, nmax))


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

    tmp_dir = tempfile.mkdtemp()

    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"images-{timestamp}.zip"
    filepath = f'{tmp_dir}/{filename}'

    compress_directory(AppConfig.get_output_dir(), filepath)

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
        inserted_images = insert_images_from_backup(tmp_dir)

        delete_directory(tmp_dir)

        text = f'{len(inserted_images)} new images has been uploaded'
        nmax = min(AppConfig.get_images_per_page(), len(inserted_images))

        return template_and_search_terms(text, inserted_images[:nmax])

    else:
        error_message = 'The uploaded file is not a zip file!'
        return template('error.html', error_message=error_message)


def run_server():
    app.run(host='0.0.0.0', port=AppConfig.get_port())


if __name__ == '__main__':
    AppConfig()
    conf_logging()
    logger = logging.getLogger("app")

    logger.info("Starting ...")
    clean_database()

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