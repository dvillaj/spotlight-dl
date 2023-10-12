import logging
from utils import *


def run_web_server():
    from bottle import Bottle, template, TEMPLATE_PATH, request

    app = Bottle()
    config = init_configuration()

    startup_time = get_current_time()

    @app.route('/')
    def index():
        images = read_images_database()
        return template_and_search_terms(startup_time, "Latest downloaded images", images, "/")

    @app.route('/search')
    def search():
        from urllib.parse import quote

        search_term = request.query.get('search-term').encode('latin1').decode('utf-8').strip()

        image_list = search_term_database(search_term)
        len_images = len(image_list)
        text = f"{len_images} {'images' if len_images != 1 else 'image'} found with '{search_term}' term"

        return template_and_search_terms(startup_time, text, image_list, f"/search?search-term={quote(search_term)}")

    @app.route('/random')
    def index():
        from random import sample

        images = read_images_database()
        nmax = min(config.get_images_per_page(), len(images))

        return template_and_search_terms(startup_time, "Some random images", sample(images, nmax), "/random")

    @app.route('/new')
    def index():
        id_new = request.query.get('id').strip()

        inserted_images = search_id_database(id_new)
        text = f'{len(inserted_images)} new images has been uploaded'

        return template_and_search_terms(startup_time, text, inserted_images, f"/new?id={id_new}")

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

        compress_directory(config.get_output_dir(), filepath)

        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return static_file(filename, root=os.path.dirname(filepath), download=filename)

    @app.route('/uploadFile', method='POST')
    def upload():
        from bottle import request, redirect
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

            id_new = generate_id()
            decompress_zipfile(file_path, tmp_dir)
            insert_images_from_backup(tmp_dir, id_new)

            delete_directory(tmp_dir)
            redirect(f'/new?id={id_new}')

        else:
            error_message = 'The uploaded file is not a zip file!'
            return template('error.html', error_message=error_message)

    @app.route('/image/<hash>')
    def get_image(hash):
        import os
        from bottle import response

        logger = logging.getLogger("image")
        images = search_digest_database(hash)

        try:
            if len(images) == 0:
                raise Exception("Image not found!")

            image_path = images[0]['image_full_path']
            logger.info(f"Reading image from {image_path} ...")

            if not os.path.isfile(image_path):
                raise Exception("Image file not found!")

            response.content_type = 'image/jpeg'

            with open(image_path, 'rb') as f:
                image_data = f.read()

            return image_data

        except BaseException as e:
            return template('error.html', error_message=e)

    TEMPLATE_PATH.append('./templates')
    app.run(host='0.0.0.0', port=config.get_port())


def main():
    import multiprocessing
    import traceback

    init_configuration()
    conf_logging()
    logger = logging.getLogger("app")

    logger.info("Starting ...")
    logger.info(f"Reading database from {AppConfig.get_output_dir()}")
    clean_database()

    server_process = multiprocessing.Process(target=run_web_server)
    server_process.start()

    logger.info(f"Web Server started ...")

    setup_output_dir()
    initial_sleep()

    try:
        n = 1
        images = count_images_database()

        while True:
            logger.info(f"Iteration {n} - Images {images} ...")
            for item in get_images_data():
                if process_image(item):
                    images = images + 1
                    send_new_image_email_notification(item, images)
                    send_new_image_telegram_notification(item, images)

            sleep()
            n = n + 1

    except BaseException as e:
        logger.info(f"Error in main process: {e}")
        traceback.print_exc()

        server_process.terminate()
        server_process.join()


if __name__ == '__main__':
    main()