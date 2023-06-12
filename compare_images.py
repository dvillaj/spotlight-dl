from utils import *


def measure_time(func):
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Executing time:", elapsed_time, "seconds")
        return result
    return wrapper


@measure_time
def compare_all_images():
    import logging
    from itertools import combinations

    logger = logging.getLogger("compare_all_images")
    logger.info("Comparing images ...")

    images = {}
    for _, image_path in get_jpg_files(AppConfig.get_output_dir()):
        logger.info(f"Processing {image_path} ...")
        images[image_path] = get_image_array(image_path)

    probs = []
    combinations = [c for c in list(combinations(images.keys(), 2)) if c[0] != c[1]]

    logger.info(f"Combinations: {len(combinations)}")
    for file1, file2 in combinations:
        logger.debug(f"Comparing {file1} with {file2} ...")
        prob = compare_images(images[file1], images[file2])
        probs.append((file1, file2, prob))

    for file1, file2 in combinations:
        prob = compare_images(images[file1], images[file2])
        probs.append((file1, file2, prob))

    for image1, image2, prob in sorted(combinations, key=lambda x: x[2], reverse=True):
        logger.info(f"{image1} - {image2} - {prob}")



init_configuration()
conf_logging()

compare_all_images()