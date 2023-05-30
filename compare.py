import cv2

def compare_images(image1_path, image2_path):
    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)

    diff = cv2.absdiff(image1, image2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    similarity = 1.0 - (len(contours) / 5000.0)
    return similarity


# Ruta de las imágenes a comparar
image1_path = 'c:/tmp/f0475b4709bad02e5392fb0295ae1ff8.jpg'
image2_path = 'c:/tmp/images/Unknown/ee20c85d15b2f05dfc1dc527169aefee.jpg'

# Comparar las imágenes
similarity = compare_images(image1_path, image2_path)
print(f"Probabilidad de similitud: {similarity}")