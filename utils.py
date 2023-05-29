class AppConfig:
    config = None
    countries = None

    def __init__(self):
        import yaml

        if not AppConfig.config:
            with open("settings.yaml", "r") as f:
                AppConfig.config = yaml.safe_load(f)

        if not AppConfig.countries:
            AppConfig.countries = self.get_countries()

    @staticmethod
    def get_port():
        return AppConfig.config['general']['port']

    @staticmethod
    def get_url(country):
        from datetime import datetime

        url = AppConfig.config['spotlight']['url']
        pid = AppConfig.config['spotlight']['pid']
        language = AppConfig.get_language()

        return (url
                .replace("${pid}", str(pid))
                .replace("${time}", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
                .replace("${country}", country)
                .replace("${language}", language)
                )

    @staticmethod
    def get_country_name(code):
        return AppConfig.countries[code.upper()]

    @staticmethod
    def get_ad():
        return AppConfig.config['ad']

    @staticmethod
    def get_country():
        import os

        try:
            env_country = os.getenv('COUNTRY')
            if env_country:
                country = env_country.upper()
            else:
                country = AppConfig.config['spotlight']['country'].upper()

            if country == "RANDOM":
                return AppConfig.get_random_country()
            else:
                return country

        except KeyError:
            return AppConfig.get_random_country()

    @staticmethod
    def get_random_country():
        import random
        country_keys = list(AppConfig.countries.keys())
        return random.choice(country_keys)

    @staticmethod
    def get_language():
        import os

        env_language = os.getenv('LANGUAGE')
        if env_language:
            return env_language
        else:
            return AppConfig.config['spotlight']['language']

    @staticmethod
    def get_images_per_page():
        import os

        env_images = os.getenv('IMAGES_PER_PAGE')
        if env_images:
            return int(env_images)
        else:
            return AppConfig.config['general']['imagesPerPage']

    @staticmethod
    def get_json_filename():
        return AppConfig.config['general']['json.filename']

    @staticmethod
    def get_output_dir():
        import os

        output_dir = os.getenv('OUTPUT_DIR')
        if output_dir:
            return output_dir
        else:
            return AppConfig.config['general']['output.dir']

    @staticmethod
    def get_sleep_time():
        import os

        sleep_time = os.getenv('SLEEP_TIME')
        if sleep_time:
            return int(sleep_time)
        else:
            return int(AppConfig.config['general']['sleep.time'])

    @staticmethod
    def get_initial_sleep():
        import os

        sleep_time = os.getenv('INITIAL_SLEEP')
        if sleep_time:
            return int(sleep_time)
        else:
            return int(AppConfig.config['general']['initial.sleep.time'])

    @staticmethod
    def get_countries():
        import json
        with open("data/countries.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return data


def check_file_exists(file: str) -> bool:
    from os.path import exists

    return exists(file)


def conf_logging(config_file: str = 'logging.ini'):
    import logging
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
    import logging

    logger = logging.getLogger("clean_database")
    try:

        country = AppConfig.get_country()
        data = requests.get(AppConfig.get_url(country)).json()

        if 'items' in data['batchrsp']:
            for i, items in enumerate(data['batchrsp']['items']):
                mi_diccionario = json.loads(items['item'])['ad']

                image_url_landscape = mi_diccionario['image_fullscreen_001_landscape']['u']
                image_url_portrait = mi_diccionario['image_fullscreen_001_portrait']['u']
                title = get_text(mi_diccionario, 'title_text')

                if not title:
                    title = "Unknown"

                hs1_title = get_text(mi_diccionario, 'hs1_title_text')
                hs2_title = get_text(mi_diccionario, 'hs2_title_text')
                hs1_cta_text = get_text(mi_diccionario, 'hs1_cta_text')
                hs2_cta_text = get_text(mi_diccionario, 'hs2_cta_text')
                copyright_text = get_text(mi_diccionario, 'copyright_text')

                description = f"{join_lines(hs1_title, hs1_cta_text)}. {join_lines(hs2_title, hs2_cta_text)}"
                if description.strip() == ".":
                    description = ""

                for ad_text in AppConfig.get_ad():
                    if ad_text in description:
                        description = ""

                yield {"image_url_landscape": image_url_landscape, "image_url_portrait": image_url_portrait,
                       "title": title, "description": description, "copyright": copyright_text,
                       "hs1_title": hs1_title, "hs2_title": hs2_title, "hs1_cta_text": hs1_cta_text,
                       "hs2_cta_text": hs2_cta_text,
                       "country": country, "country_name": AppConfig.get_country_name(country)
                       }

    except Exception as error:
        logger.error(f"Error requesting images: {error}")


def get_text(dictionary, key):
    try:
        return dictionary[key]['tx']
    except KeyError:
        return ''


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

    dirs = image_json['title'].split(",")
    dirs.reverse()
    dirs = [s.strip() for s in dirs]
    dirs = "/".join(dirs)

    image_path = f"{dirs}/{image_json['hex_digest']}.jpg"
    full_name = f"{AppConfig.get_output_dir()}/{image_path}"

    if not os.path.exists(os.path.dirname(full_name)):
        os.makedirs(os.path.dirname(full_name))

    image_json['image_path'] = image_path
    image_json['image_full_path'] = full_name


def get_digest(image_json):
    return image_json['hex_digest']


def get_title(image_json):
    return image_json['title']


def get_description(image_json):
    return image_json['description']


def clean_database():
    import logging
    logger = logging.getLogger("clean_database")
    database = read_images_database()

    logger.debug(f"Clean database {get_json_database_name()} ...")

    remove_database()
    delete_unknown_directory()

    for json in database:
        add = True
        digest = get_digest(json)
        title = get_title(json)
        description = get_description(json)
        for ad_text in AppConfig.get_ad():
            if ad_text in description:
                logger.info(f"Clean description: {description} at {title} / {digest} image")
                json['description'] = ""

        image_full_path = f"{AppConfig.get_output_dir()}/{json['image_path']}"

        if not check_file_exists(image_full_path):
            logger.error(f"{image_full_path} DO NOT EXISTS!")
            add = process_image(json)

        if add:
            add_image_to_database(json)


def exists_image(json_image):
    import logging
    logger = logging.getLogger("exists_image")
    database = read_images_database()

    digest = get_digest(json_image)
    image_title = get_title(json_image)
    image_description = get_description(json_image)
    logger.debug(f"Searching for {digest} / {image_title} in {len(database)} images database ...")

    for json in database:
        database_digest = get_digest(json)
        database_title = get_title(json)
        database_description = get_description(json)
        if database_digest == digest:
            if (database_title == "Unknown" and database_title != image_title or
                    database_description == "" and image_description != ""):
                logger.info(f"Upgrading an image: {image_title} / {digest}")
            else:
                logger.debug(f"Image {digest} found!")
                return True

    logger.debug(f"Image {image_title} / {digest} not found!")
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
    import logging

    logger = logging.getLogger("sleep")

    seconds = AppConfig.get_sleep_time()

    logger.info(f"Sleeping {seconds} seconds ...")
    time.sleep(seconds)


def count_images_database():
    return len(read_images_database())


def read_images_database(locationPath=None):
    from datetime import datetime
    import json
    import os

    json_database = get_json_database_name(locationPath)

    images_json = {}

    if os.path.isfile(json_database):
        with open(json_database, 'r') as archivo_jsonl:
            for line in archivo_jsonl:
                json_line = json.loads(line)

                if 'description' not in json_line:
                    json_line['description'] = ""

                if 'country' not in json_line:
                    json_line['country'] = "Unknown"

                if 'country_name' not in json_line:
                    json_line['country_name'] = AppConfig.get_country_name(json_line['country'])

                hex_digest = json_line['hex_digest']
                images_json[hex_digest] = json_line

    return sorted([images_json[key] for key in images_json], reverse=True,
                  key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%dT%H:%M:%S.%f'))


def get_now():
    import datetime

    return datetime.datetime.now().isoformat()


def get_json_database_name(locationPath=None):
    if locationPath is None:
        location = AppConfig.get_output_dir()
    else:
        location = locationPath

    return f"{location}/{AppConfig.get_json_filename()}"


def remove_database():
    import logging
    import os

    logger = logging.getLogger("remove_database")
    database_name = get_json_database_name()

    if os.path.exists(database_name):
        os.remove(database_name)
        logger.info(f"Removing database: {database_name}")


def add_image_to_database(image_json):
    import json
    import logging

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
    import logging

    logger = logging.getLogger("initial_sleep")

    sleep_time = AppConfig.get_initial_sleep()
    if sleep_time:
        logger.info(f"Sleeping {sleep_time} seconds ...")
        time.sleep(int(sleep_time))


def setup_output_dir():
    import os
    import logging

    logger = logging.getLogger("setup_output_dir")

    output_dir = AppConfig.get_output_dir()

    logger.info(f"Output dir: {output_dir}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output dir created!")

    os.system(f'chmod u+rwx {output_dir}')
    logger.info("Output dir configured!")


def copy_file(source_path, destination_path):
    import shutil
    import logging

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
    import logging

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
    import logging

    logger = logging.getLogger("decompress_file")

    try:
        with zipfile.ZipFile(archive_path, "r") as zipf:
            zipf.extractall(path=output_directory)

        logger.info(f"Archive '{archive_path}' extracted to '{output_directory}' successfully.")
    except Exception as e:
        logger.error(f"Error extracting archive '{archive_path}': {e}")
        raise e


def delete_directory(directory):
    import logging
    import shutil

    logger = logging.getLogger("delete_directory")
    try:
        shutil.rmtree(directory)
        logger.info(f"Directory {directory} and its contents have been successfully deleted.")
    except Exception as e:
        logger.error(f"Error deleting the directory {directory}: {e}")
        raise e


def delete_unknown_directory():
    import logging
    import os
    import shutil

    logger = logging.getLogger("delete_unknown_directory")
    image_path = f"Unknown"
    path = f"{AppConfig.get_output_dir()}/{image_path}"
    logger.info(f"Deleting {path} directory ...")

    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"Directory '{path}' removed successfully!")
        else:
            logger.debug(f"File '{path}' not found!")

    except OSError as e:
        logger.error(f"Error removing directory: {path}")


def delete_unknown_image(image_json):
    import logging
    import os

    logger = logging.getLogger("delete_unknown_image")
    image_path = f"Unknown/{image_json['hex_digest']}.jpg"
    path = f"{AppConfig.get_output_dir()}/{image_path}"

    if os.path.exists(path):
        os.remove(path)
        logger.info(f"File '{path}' removed successfully!")
    else:
        logger.debug(f"File '{path}' not found!")


def process_image(image_json):
    import logging

    logger = logging.getLogger("process_image")
    try:
        download_image(image_json)
        if not exists_image(image_json):
            delete_unknown_image(image_json)
            save_image(image_json)
            tag_image(image_json)

            add_image_to_database(image_json)

            logger.info(f"Downloaded {image_json['title']} into {image_json['image_full_path']} ...")
            return True

    except Exception as error:
        logger.error(f"Error processing image {image_json['title']}: {error} ")

    return False


def insert_images_from_backup(backup_dir):
    import logging
    import json

    logger = logging.getLogger("insert_images_from_backup")

    logger.info(f"Backup Dir: {backup_dir}")
    images = read_images_database(backup_dir)

    inserted_images = []
    for image in images:
        logger.debug(json.dumps(image, indent=3))
        if not exists_image(image):
            logger.info(f"Adding image: {image['title']}")

            from_path = f"{backup_dir}/{image['image_path']}"
            if not check_file_exists(from_path):
                logger.error(f"{from_path} DO NOT EXISTS: \n{json.dumps(image, indent=3)}")
                process_image(image)

            else:
                make_image_directory(image)

                copy_file(from_path, image['image_full_path'])
                image['timestamp'] = get_now()
                add_image_to_database(image)

                inserted_images.append(image)

    logger.info(f"Inserted {len(inserted_images)} of {len(images)} images!")
    return inserted_images


def get_file_count(directory):
    import os
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count


def get_links(grouped_terms=[]):
    import os

    images_dir = AppConfig.get_output_dir()

    subdirectories = []
    term_counts = {term: 0 for term in grouped_terms}

    for name in os.listdir(images_dir):
        subdir_path = os.path.join(images_dir, name)
        if os.path.isdir(subdir_path):
            for term in grouped_terms:
                if term.lower() in name.lower():
                    term_counts[term] += get_file_count(subdir_path)
                    break
            else:
                file_count = get_file_count(subdir_path)
                subdirectories.append((name, file_count))

    for term, count in term_counts.items():
        if count:
            subdirectories.append((term, count))

    return sorted(subdirectories, key=lambda x: x[1], reverse=True)


def template_and_search_terms(text, image_list):
    from bottle import template
    images = read_images_database()
    search_terms = get_links(grouped_terms=["Painting", "Galaxy"])

    return template('index.html', counter=len(images), text=text, imagelist=image_list, search_terms=search_terms)


def search_term_database(search_term):
    images = read_images_database()
    return [item for item in images if search_term.lower() in (
            item['title'] + item['description'] + item['hex_digest'] + item['timestamp']).lower()]
