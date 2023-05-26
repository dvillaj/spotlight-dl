class AppConfig:
    def __init__(self):
        import yaml
        with open("settings.yaml", "r") as f:
            self.config = yaml.safe_load(f)

    def get_url(self):
        from datetime import datetime

        url = self.config['spotlight']['url']
        pid = self.config['spotlight']['pid']
        country = self.get_country()
        language = self.get_language()

        return (url
                .replace("${pid}", str(pid))
                .replace("${time}", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
                .replace("${country}", country)
                .replace("${language}", language)
          )

    def get_country(self):
        import os

        try:
            env_country = os.getenv('COUNTRY')
            if env_country:
                country = env_country
            else:
                country = self.config['spotlight']['country']

            if country == "random":
                return random_country_code().lower()
            else:
                return country

        except KeyError:
            return random_country_code().lower()

    def get_language(self):
        import os

        env_language = os.getenv('LANGUAGE')
        if env_language:
            return env_language
        else:
            return self.config['spotlight']['language']

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

    config = AppConfig()
    data = requests.get(config.get_url()).json()

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

            description = f"{title}. {join_lines(hs1_title, hs1_cta_text)}. {join_lines(hs2_title, hs2_cta_text)}"
            if "Microsoft" in description or "AI" in description:
                description = title

            yield {"image_url_landscape": image_url_landscape, "image_url_portrait": image_url_portrait,
                   "title": title, "description": description, "copyright": copyright_text,
                   "hs1_title": hs1_title, "hs2_title": hs2_title, "hs1_cta_text": hs1_cta_text, "hs2_cta_text": hs2_cta_text
                   }


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
    import logging
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
    import logging

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

    config = AppConfig()
    sleep_time = config.get_initial_sleep()
    if sleep_time:
        logger.info(f"Sleeping {sleep_time} seconds ...")
        time.sleep(int(sleep_time))


def setup_output_dir():
    import os
    import logging

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


def process_image(image_json):
    import logging

    logger = logging.getLogger("process_image")
    download_image(image_json)
    if not exists_image(get_digest(image_json)):
        save_image(image_json)
        tag_image(image_json)

        add_image_to_database(image_json)

        logger.info(f"Downloaded {image_json['title']} into {image_json['image_full_path']} ...")
        return True

    return False


def insert_images_from_backup(backup_dir):
    import logging
    import json

    logger = logging.getLogger("insert_images_from_backup")

    logger.info(f"Backup Dir: {backup_dir}")
    images = read_images_database(backup_dir)

    inserted = 0
    for image in images:
        logger.debug(json.dumps(image, indent=3))
        if not exists_image(get_digest(image)):
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

            inserted = inserted + 1

    logger.info(f"Inserted {inserted} of {len(images)} images!")
    return inserted


def country_codes():
    return [
        'AF', 'AX', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG', 'AR', 'AM', 'AW', 'AU', 'AT', 'AZ', 'BS', 'BH', 'BD',
        'BB', 'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT', 'BO', 'BQ', 'BA', 'BW', 'BV', 'BR', 'IO', 'BN', 'BG', 'BF', 'BI', 'KH',
        'CM', 'CA', 'CV', 'KY', 'CF', 'TD', 'CL', 'CN', 'CX', 'CC', 'CO', 'KM', 'CG', 'CD', 'CK', 'CR', 'CI', 'HR', 'CU',
        'CW', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO', 'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'ET', 'FK', 'FO', 'FJ', 'FI', 'FR',
        'GF', 'PF', 'TF', 'GA', 'GM', 'GE', 'DE', 'GH', 'GI', 'GR', 'GL', 'GD', 'GP', 'GU', 'GT', 'GG', 'GN', 'GW', 'GY',
        'HT', 'HM', 'VA', 'HN', 'HK', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 'IT', 'JM', 'JP', 'JE', 'JO',
        'KZ', 'KE', 'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 'LI', 'LT', 'LU', 'MO', 'MK', 'MG',
        'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT', 'MX', 'FM', 'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ',
        'MM', 'NA', 'NR', 'NP', 'NL', 'NC', 'NZ', 'NI', 'NE', 'NG', 'NU', 'NF', 'MP', 'NO', 'OM', 'PK', 'PW', 'PS', 'PA',
        'PG', 'PY', 'PE', 'PH', 'PN', 'PL', 'PT', 'PR', 'QA', 'RE', 'RO', 'RU', 'RW', 'BL', 'SH', 'KN', 'LC', 'MF', 'PM',
        'VC', 'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC', 'SL', 'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS', 'SS', 'ES',
        'LK', 'SD', 'SR', 'SJ', 'SZ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TK', 'TO', 'TT', 'TN', 'TR',
        'TM', 'TC', 'TV', 'UG', 'UA', 'AE', 'GB', 'US', 'UM', 'UY', 'UZ', 'VU', 'VE', 'VN', 'VG', 'VI', 'WF', 'EH', 'YE',
        'ZM', 'ZW'
    ]


def random_country_code():
    import random

    return random.choice(country_codes())

