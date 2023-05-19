import logging
import threading
from bottle import Bottle, template, TEMPLATE_PATH


class AppConfig:
    def __init__(self):
        import yaml
        with open("settings.yaml", "r") as f:
            self.config = yaml.safe_load(f)

    def get_url(self):
        return self.config['spotlight']['url']

    def get_json_filename(self):
        return self.config['general']['json.filename']

    def get_output_dir(self):
        import os

        output_dir = os.getenv('OUTPUT_DIR')
        if output_dir:
            return output_dir
        else:
            return self.config['general']['output.dir']

    def get_sleep_time(self):
        import os

        sleep_time = os.getenv('SLEEP_TIME')
        if sleep_time:
            return int(sleep_time)
        else:
            return int(self.config['general']['sleep.time'])

    def get_initial_sleep(self):
        import os

        sleep_time = os.getenv('INITIAL_SLEEP')
        if sleep_time:
            return int(sleep_time)
        else:
            return int(self.config['general']['initial.sleep.time'])


def check_file_exists(file: str) -> bool:
    from os.path import exists

    return exists(file)


def conf_logging(config_file: str = 'logging.ini'):
    from logging.config import fileConfig
    import os

    if check_file_exists(config_file):
        fileConfig(config_file)

        log_level = os.environ.get('LOG_LEVEL', None)
        if log_level:
            logging.getLogger().setLevel(log_level)

    else:
        print("Logging config file do no exists!")


def join_lines(line1_arg, line2_arg):
    # Join line1 and line2 descriptions
    line1 = line1_arg.strip()
    line2 = line2_arg.strip()

    if line1.endswith("…"):
        return f"{line1[:-1]} {line2[0].lower()}{line2[1:]}"
    else:
        return f"{line1} {line2}"


def get_images_data():
    import requests
    import json

    config = AppConfig()
    data = requests.get(config.get_url()).json()

    for i, items in enumerate(data['batchrsp']['items']):
        mi_diccionario = json.loads(items['item'])['ad']

        image_url_landscape = mi_diccionario['image_fullscreen_001_landscape']['u']
        image_url_portrait = mi_diccionario['image_fullscreen_001_portrait']['u']
        title = mi_diccionario['title_text']['tx']
        hs1_title = mi_diccionario['hs1_title_text']['tx']
        hs2_title = mi_diccionario['hs2_title_text']['tx']
        hs1_cta_text = mi_diccionario['hs1_cta_text']['tx']
        hs2_cta_text = mi_diccionario['hs2_cta_text']['tx']
        copyright_text = mi_diccionario['copyright_text']['tx']

        description = f"{title}. {join_lines(hs1_title, hs1_cta_text)}. {join_lines(hs2_title, hs2_cta_text)}"
        if "Microsoft" in description or "AI" in description:
            description = title

        yield {"image_url_landscape": image_url_landscape, "image_url_portrait": image_url_portrait,
               "title": title, "description": description, "copyright": copyright_text,
               "hs1_title": hs1_title, "hs2_title": hs2_title, "hs1_cta_text": hs1_cta_text, "hs2_cta_text": hs2_cta_text
               }


def download_image(image_json):
    import requests
    from io import BytesIO
    from hashlib import md5

    image_response = requests.get(image_json['image_url_landscape'])
    image_data = BytesIO(image_response.content)

    md5sum = md5(image_data.getbuffer())
    hex_digest = md5sum.hexdigest()

    image_json['hex_digest'] = hex_digest
    image_json['image_data'] = image_data


def save_image(image_json):
    from PIL import Image

    make_image_directory(image_json)

    image = Image.open(image_json['image_data'])
    image.save(image_json['image_full_path'])


def make_image_directory(image_json):
    import os

    config = AppConfig()

    dirs = image_json['title'].split(",")
    dirs.reverse()
    dirs = [s.strip() for s in dirs]
    dirs = "/".join(dirs)

    image_path = f"{dirs}/{image_json['hex_digest']}.jpg"
    full_name = f"{config.get_output_dir()}/{image_path}"

    if not os.path.exists(os.path.dirname(full_name)):
        os.makedirs(os.path.dirname(full_name))

    image_json['image_path'] = image_path
    image_json['image_full_path'] = full_name


def get_digest(image_json):
    return image_json['hex_digest']


def exists_image(digest):
    logger = logging.getLogger("exists_image")
    database = read_images_database()

    logger.debug(f"Searching {digest} info {len(database)} images ...")

    for json in database:
        if 'hex_digest' in json and json['hex_digest'] == digest:
            logger.debug("Found!")
            return True

    logger.debug("Not found!")
    return False


def tag_image(image_json):
    import exif

    image_name = image_json['image_full_path']

    with open(image_name, 'rb') as img_file:
        img = exif.Image(img_file)

    img.image_description = image_json['description'].encode('ascii', 'ignore').decode()
    img.copyright = image_json['copyright'].encode('ascii', 'ignore').decode()

    with open(image_name, 'wb') as new_image_file:
        new_image_file.write(img.get_file())


def sleep():
    import time

    logger = logging.getLogger("sleep")

    config = AppConfig()
    seconds = config.get_sleep_time()

    logger.info(f"Sleeping {seconds} seconds ...")
    time.sleep(seconds)


def count_images_database():
    return len(read_images_database())


def read_images_database(locationPath = None):
    from datetime import datetime
    import json
    import os

    json_database = get_json_database_name(locationPath)

    images_json = []

    if os.path.isfile(json_database):
        with open(json_database, 'r') as archivo_jsonl:
            for line in archivo_jsonl:
                json_line = json.loads(line)
                images_json.append(json_line)

    return sorted(images_json, reverse=True, key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%dT%H:%M:%S.%f'))


def get_now():
    import datetime

    return datetime.datetime.now().isoformat()


def get_json_database_name(locationPath = None):
    config = AppConfig()
    if locationPath is None:
        location = config.get_output_dir()
    else:
        location = locationPath

    return f"{location}/{config.get_json_filename()}"


def add_image_to_database(image_json):
    import json

    logger = logging.getLogger("add_image_to_database")
    json_database = get_json_database_name()

    if 'image_data' in image_json:
        del image_json['image_data']

    image_json['timestamp'] = get_now()
    with open(json_database, 'a') as file:
        file.write(json.dumps(image_json))
        file.write("\n")

    logger.debug(f"Save data to {json_database} ..")


def initial_sleep():
    import time

    logger = logging.getLogger("initial_sleep")

    config = AppConfig()
    sleep_time = config.get_initial_sleep()
    if sleep_time:
        logger.info(f"Sleeping {sleep_time} seconds ...")
        time.sleep(int(sleep_time))


def setup_output_dir():
    import os

    logger = logging.getLogger("setup_output_dir")
    config = AppConfig()

    output_dir = config.get_output_dir()

    logger.info(f"Output dir: {output_dir}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output dir created!")

    os.system(f'chmod u+rwx {output_dir}')
    logger.info("Output dir configured!")


def copy_file(source_path, destination_path):
    import shutil

    logger = logging.getLogger("copy_file")

    try:
        shutil.copy2(source_path, destination_path)
        logger.info(f"File copied from {source_path} to {destination_path} successfully.")
    except IOError as e:
        logger.error(f"Error copying the file: {e}")
        raise e


def compress_directory(directory_path, output_filename):
    import zipfile
    import os

    logger = logging.getLogger("compress_directory")

    try:
        with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory_path)
                    zipf.write(file_path, arcname)

        logger.info(f"Directory '{directory_path}' compressed to '{output_filename}' successfully.")
    except Exception as e:
        logger.error(f"Error compressing directory '{directory_path}': {e}")
        raise e


def decompress_zipfile(archive_path, output_directory):
    import zipfile

    logger = logging.getLogger("decompress_file")

    try:
        with zipfile.ZipFile(archive_path, "r") as zipf:
            zipf.extractall(path=output_directory)

        logger.info(f"Archive '{archive_path}' extracted to '{output_directory}' successfully.")
    except Exception as e:
        logger.error(f"Error extracting archive '{archive_path}': {e}")
        raise e


def delete_directory(directory):
    import shutil

    logger = logging.getLogger("delete_directory")
    try:
        shutil.rmtree(directory)
        logger.info(f"Directory {directory} and its contents have been successfully deleted.")
    except Exception as e:
        logger.error(f"Error deleting the directory {directory}: {e}")
        raise e


app = Bottle()
TEMPLATE_PATH.append('./templates')


@app.route('/')
def index():
    images = read_images_database()
    nmax = min(10, len(images))

    return template('index.html', counter=len(images), imagelist=images[:nmax], text="Last downloaded images")


@app.route('/random')
def index():
    from random import sample

    images = read_images_database()
    nmax = min(10, len(images))

    return template('index.html', counter=len(images), imagelist=sample(images, nmax), text="Some random images")


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
    import json

    logger = logging.getLogger("uploadFile")
    config = AppConfig()

    upload = request.files.get('filename')
    filename = upload.filename
    if '.zip' in filename:
        tmp_dir = tempfile.mkdtemp()
        logger.debug(f"Temp path: {tmp_dir}")
        file_path = os.path.join(tmp_dir, filename)
        upload.save(file_path)

        decompress_zipfile(file_path, tmp_dir)

        tmp_path = f"{tmp_dir}"
        images = read_images_database(tmp_path)

        inserted = 0

        for image in images:
            logger.debug(json.dumps(image, indent = 3))
            if not exists_image(get_digest(image)):
                logger.info(f"Adding image: {image['title']}")

                from_path = f"{tmp_path}/{image['image_path']}"
                make_image_directory(image)

                copy_file(from_path, image['image_full_path'])
                image['timestamp'] = get_now()
                add_image_to_database(image)
                inserted = inserted + 1

        delete_directory(tmp_dir)

        return f'File {filename} has been processed successfully with {len(images)} images ({inserted} new)'
    else:
        return 'The upload file is not a zip file!'


def run_server():
    app.run(host='0.0.0.0', port=8000)


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
            download_image(item)
            if not exists_image(get_digest(item)):
                save_image(item)
                tag_image(item)

                add_image_to_database(item)

                images = images + 1

                logger.info(f"Downloaded {item['title']} into {item['image_full_path']} ...")

        sleep()
        n = n + 1