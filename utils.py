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
        return AppConfig.get_configuration_item('general', 'port')

    @staticmethod
    def get_home_url():
        url = AppConfig.get_configuration_item('general', 'home.url').strip()
        if not url.endswith("/"):
            return url + "/"
        else:
            return url

    @staticmethod
    def get_spotlight_url(country):
        from datetime import datetime

        url = AppConfig.get_configuration_item('spotlight', 'url')
        pid = AppConfig.get_configuration_item('spotlight', 'pid', AppConfig.get_random_pid())
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
        return AppConfig.get_configuration_item('spotlight', 'country', AppConfig.get_random_country()).upper()

    @staticmethod
    def get_random_country():
        import random
        country_keys = list(AppConfig.countries.keys())
        return random.choice(country_keys)

    @staticmethod
    def get_notification_email_images():
        return int(AppConfig.get_configuration_item('notification.email', 'images', 0))

    @staticmethod
    def get_notification_email_sender():
        return AppConfig.get_configuration_item('notification.email', 'sender', "")

    @staticmethod
    def get_notification_email_password():
        return AppConfig.get_configuration_item('notification.email', 'password', "")

    @staticmethod
    def get_notification_telegram_images():
        return int(AppConfig.get_configuration_item('notification.telegram', 'images', 0))

    @staticmethod
    def get_notification_telegram_token():
        return AppConfig.get_configuration_item('notification.telegram', 'token', "")

    @staticmethod
    def get_notification_telegram_chat_id():
        return AppConfig.get_configuration_item('notification.telegram', 'chatId', "")

    @staticmethod
    def get_language():
        return AppConfig.get_configuration_item('spotlight', 'language')

    @staticmethod
    def get_images_per_page():
        return int(AppConfig.get_configuration_item('general', 'imagesPerPage'))

    @staticmethod
    def get_json_filename():
        return AppConfig.get_configuration_item('general', 'json.filename')

    @staticmethod
    def get_output_dir():
        return AppConfig.get_configuration_item('general', 'output.dir')

    @staticmethod
    def get_sleep_time():
        return int(AppConfig.get_configuration_item('general', 'sleep.time'))

    @staticmethod
    def get_initial_sleep():
        return int(AppConfig.get_configuration_item('general', 'initial.sleep.time'))

    @staticmethod
    def get_countries():
        import json
        with open("data/countries.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    @staticmethod
    def get_configuration_item(section, item, default_value = None):
        import os

        value = os.getenv(f"SPOTLIGHTDL_{section}.{item}".replace('.','_').upper())
        if not value:
            try:
                value = AppConfig.config[section][item]
            except:
                if default_value is not None:
                    return f"{default_value}"
                else:
                    raise ValueError(f"Error reading configuration: Item '{item}' from section '{section}' not found!")

        return value

    @staticmethod
    def get_random_pid(lower_bound = 200000, upper_bound = 209999):
        import random
        import time

        random.seed(int(time.time()))
        return random.randint(lower_bound, upper_bound)


def check_file_exists(file: str) -> bool:
    from os.path import exists

    return exists(file)


def init_configuration():
    return AppConfig()


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
    import traceback

    logger = logging.getLogger("get_images_data")
    try:

        country = AppConfig.get_country()
        data = requests.get(AppConfig.get_spotlight_url(country)).json()

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

    except BaseException as error:
        logger.error(f"Error requesting images: {error}")
        traceback.print_exc()


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


def get_timestamp(image_json):
    return image_json['timestamp']


def get_description(image_json):
    return image_json['description']


def clean_database():
    import logging
    logger = logging.getLogger("clean_database")
    database = read_images_database()

    logger.info(f"Cleaning {len(database)} items of {get_json_database_name()} database ...")

    remove_database()
    delete_unknown_directory()

    for json in database:
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
            process_image(json)
        else:
            add_image_to_database(json)

    insert_images_from_home()
    check_images_count()


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

    if not 'timestamp' in image_json:
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
    except BaseException as e:
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
    except BaseException as e:
        logger.error(f"Error extracting archive '{archive_path}': {e}")
        raise e


def delete_directory(directory):
    import logging
    import shutil

    logger = logging.getLogger("delete_directory")
    try:
        shutil.rmtree(directory)
        logger.info(f"Directory {directory} and its contents have been successfully deleted.")
    except BaseException as e:
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
    import traceback

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

    except BaseException as error:
        logger.error(f"Error processing image {image_json['title']}: {error} ")
        traceback.print_exc()

    return False


def insert_images_from_backup(backup_dir, id_new):
    import logging
    import json

    logger = logging.getLogger("insert_images_from_backup")

    logger.info(f"Backup Dir: {backup_dir}")
    images = read_images_database(backup_dir)

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
                image['id-new'] = id_new
                add_image_to_database(image)


def get_file_count(directory):
    import os
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count


def get_file_date(directory):
    import os
    import datetime

    date = os.path.getctime(directory)
    return datetime.datetime.fromtimestamp(date)


def get_links(grouped_terms=[]):
    import os

    images_dir = AppConfig.get_output_dir()

    subdirectories = []
    term_counts = {term: 0 for term in grouped_terms}
    term_date = {}

    for name in os.listdir(images_dir):
        subdir_path = os.path.join(images_dir, name)
        if os.path.isdir(subdir_path):
            for term in grouped_terms:
                if term.lower() in name.lower():
                    term_counts[term] += get_file_count(subdir_path)
                    term_date[term] = get_file_date(subdir_path)
                    break
            else:
                file_count = get_file_count(subdir_path)
                date = get_file_date(subdir_path)
                subdirectories.append((name, file_count, date))

    for term, count in term_counts.items():
        if count:
            subdirectories.append((term, count, term_date[term]))

    return sorted(subdirectories, key=lambda x: (x[1], x[2]), reverse=True)


def template_and_search_terms(startup_time, text, image_list, href):
    from bottle import template, request
    import math

    images = read_images_database()
    search_terms = get_links(grouped_terms=["Painting", "Galaxy"])

    current_page = int(request.query.get('page', 1))
    per_page = AppConfig.get_images_per_page()
    start_index = (current_page - 1) * per_page
    end_index = start_index + per_page

    total_pages = math.ceil(len(image_list) / per_page)
    pages_to_show = min(8, total_pages)
    start_page = max(1, current_page - (pages_to_show // 2))
    end_page = start_page + pages_to_show - 1
    if end_page > total_pages:
        end_page = total_pages
        start_page = max(1, end_page - pages_to_show + 1)

    ellipsis_before = start_page > 1
    ellipsis_after = end_page < total_pages

    total_images = len(images)
    href = href + ("&" if "?" in href else "?")

    base_url = request.urlparts.scheme + "://" + request.urlparts.netloc

    return template('index.html',
                    counter=total_images,
                    text=text,
                    imagelist=image_list[start_index:end_index],
                    search_terms=search_terms,
                    current_page=current_page,
                    total_pages=total_pages,
                    start_page=start_page,
                    end_page=end_page,
                    ellipsis_before=ellipsis_before,
                    ellipsis_after=ellipsis_after,
                    base_url=base_url,
                    seconds=get_uptime_message(startup_time),
                    href=href)


def search_term_database(search_term):
    images = read_images_database()
    return [item for item in images if search_term.lower() in (
            item['title'] + item['description'] + item['hex_digest'] + item['timestamp']).lower()]


def search_digest_database(search_term):
    images = read_images_database()
    return [item for item in images if search_term == item['hex_digest']]


def search_id_database(search_term):
    images = read_images_database()
    return [item for item in images if search_term in ("" if "id-new" not in item else item['id-new'])]


def generate_id(length=10):
    import random
    import hashlib
    import time

    current_time = int(time.time())
    seed = random.randint(0, current_time)
    md5_hash = hashlib.md5()
    md5_hash.update(str(seed).encode('utf-8'))
    return md5_hash.hexdigest()[:length]


def get_mail_template(file):
    return f"templates/{file}.html"


def get_markdown_template(file):
    return f"templates/{file}.md"


def send_new_image_email_notification(image, actual_images):
    import logging

    logger = logging.getLogger("send_new_image_email_notification")

    sender = AppConfig.get_notification_email_sender()
    passwd = AppConfig.get_notification_email_password()
    images = AppConfig.get_notification_email_images()

    if images == 0:
        return

    if actual_images < images:
        logger.info(f"No enough images to send an email notification {actual_images}/{images}!")
        return

    if not passwd:
        logger.info("No password defined for email notification, so no message will be send!")
        return

    if not sender:
        logger.info("No sender defined for email notification, so no message will be send!")
        return

    subject = f"A new image has been downloaded from spotlight-dl"
    notification_template = get_mail_template("new-imagen-mail")

    image['time'] = get_time()
    image['actual_images'] = actual_images
    image['home_url'] = AppConfig.get_home_url()

    logger.info(f"Sending a notification to {sender} ...")
    template = get_notification_template(notification_template, image)
    send_email(sender, subject, template, sender, passwd)


def send_new_image_telegram_notification(image, actual_images):
    import logging

    logger = logging.getLogger("send_new_image_telegram_notification")

    images = AppConfig.get_notification_telegram_images()
    token = AppConfig.get_notification_telegram_token()
    chat_id = AppConfig.get_notification_telegram_chat_id()

    if images == 0:
        return

    if actual_images < images:
        logger.info(f"No enough images to send a telegram notification {actual_images}/{images}!")
        return

    if not token:
        logger.info("No token defined for telegram notification, so no message will be send!")
        return

    if not chat_id:
        logger.info("No chat_id defined for telegram notification, so no message will be send!")
        return

    notification_template = get_markdown_template("new-imagen-telegram")

    image['time'] = get_time()
    image['actual_images'] = actual_images
    image['home_url'] = AppConfig.get_home_url()

    logger.info(f"Sending a telegram notification ...")
    template = get_notification_template(notification_template, image)
    send_telegram(chat_id, token, template)


def get_time():
    from datetime import datetime

    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def get_notification_template(template_file, variables):
    from jinja2 import Environment, FileSystemLoader

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('.'))

    # Load the template
    template = env.get_template(template_file)

    # Render the template with variables
    return template.render(variables)


def send_email(recipient, subject, template, sender, password):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Set up email parameters
    email_sender = sender
    email_recipient = recipient
    email_subject = subject

    # Create MIME object
    message = MIMEMultipart("alternative")
    message['From'] = email_sender
    message['To'] = email_recipient
    message['Subject'] = email_subject

    # Attach HTML message
    html_content = MIMEText(template, 'html')
    message.attach(html_content)

    # Configure SMTP connection
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
    smtp_connection.starttls()

    # Log in to Gmail account
    smtp_connection.login(email_sender, password)

    # Send the email
    smtp_connection.sendmail(email_sender, email_recipient, message.as_string())

    # Close the SMTP connection
    smtp_connection.quit()


def send_telegram(chat_id, token, message):
    import requests
    import logging

    logger = logging.getLogger("send_telegram")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        logger.info("Telegram notification send!")
    else:
        logger.error(f"Error sending Telegram notification: {response.content}")


def get_title_from_path(path):
    clean_path = path.replace(AppConfig.get_output_dir(), "")
    name_file = clean_path.split("/")[-1]

    folders = clean_path.replace(f"/{name_file}", "").split("/")[1:]
    return ", ".join(folders[::-1])


def get_jpg_files(directory):
    import os
    jpg_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".jpg"):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                jpg_files.append((file_name.replace(".jpg", ""), file_path))

    return jpg_files


def insert_images_from_home():
    import logging

    logger = logging.getLogger("insert_images_from_home")

    logger.info("Inserting images from home directory")

    images = 0
    for digest, image_path in get_jpg_files(AppConfig.get_output_dir()):
        if not search_digest_database(digest):
            image_path = image_path.replace("\\", "/")
            image_json = {'image_url_landscape': f"./image/{digest}", 'title': get_title_from_path(image_path),
                          'description': "",
                          'copyright': "", 'country': "UNKNOWN", 'country_name': AppConfig.get_country_name("UNKNOWN"),
                          'hex_digest': digest, 'image_path': image_path.replace(f"{AppConfig.get_output_dir()}/", ""),
                          'image_full_path': image_path, 'timestamp': get_now()}

            logger.debug(f"JSON = {image_json}")
            add_image_to_database(image_json)
            images = images + 1

    logger.info(f"{images} images has been inserted from home dir!")


def check_images_count():
    import logging

    logger = logging.getLogger("check_images_count")

    logger.info("Checking images from disk...")

    images_from_disk = get_jpg_files(AppConfig.get_output_dir())
    len_images_from_disk = len(images_from_disk)
    images = read_images_database()
    len_images = len(images)

    if len_images != len_images_from_disk:
        logger.error(f"Images from disk ({len_images_from_disk}) are not equal than database ({len_images}) !!!")
        if len_images_from_disk > len_images:
            for digest, image_path in images_from_disk:
                images_databases = search_digest_database(digest)
                if not images_databases:
                    logger.error(f"Image from disk not found in database: {image_path}")

    else:
        logger.info("Images from disk are equal than database :-)")


def get_current_time():
    from datetime import datetime

    return datetime.now()


def get_uptime_message(start_time):
    from datetime import datetime

    current_seconds = int((datetime.now() - start_time).total_seconds())

    days = current_seconds // 86400
    current_seconds %= 86400

    hours = current_seconds // 3600
    current_seconds %= 3600

    minutes = current_seconds // 60
    seconds = current_seconds % 60

    message = ""

    if days > 0:
        message = f"{days} day" if days == 1 else f"{days} days"

    if hours > 0:
        message = f"{message} {hours} hour" if hours == 1 else f"{message} {hours} hours"

    if minutes > 0 and days == 0:
        message = f"{message} {minutes} minute" if minutes == 1 else f"{message} {minutes} minutes"

    if seconds > 0 and days == 0 and hours == 0:
        message = f"{message} {seconds} second" if seconds == 1 else f"{message} {seconds} seconds"

    return message
