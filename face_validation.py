import cv2
import numpy as np
from PIL import Image

FACE_DETECTOR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
EYE_DETECTOR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

EXTRA_SPACE_AROUND_FACE = 0.3
BLUR_THRESHOLD = 100.0
MIN_BRIGHTNESS = 40
MAX_BRIGHTNESS = 220


def is_too_blurry(gray_image: np.ndarray) -> bool:
    variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()
    return variance < BLUR_THRESHOLD


def is_bad_brightness(gray_image: np.ndarray) -> str | None:
    average_brightness = gray_image.mean()
    if average_brightness < MIN_BRIGHTNESS:
        return "This photo is too dark. Please retake it somewhere with better lighting."
    if average_brightness > MAX_BRIGHTNESS:
        return "This photo is too bright/overexposed. Please retake it with softer, more even lighting."
    return None


def validate_and_crop_face(image: Image.Image) -> tuple[Image.Image | None, str | None]:
    rgb_image = image.convert("RGB")
    image_as_array = np.array(rgb_image)
    gray_image = cv2.cvtColor(image_as_array, cv2.COLOR_RGB2GRAY)

    if is_too_blurry(gray_image):
        return None, "This photo looks too blurry. Please upload a sharper, more focused photo."

    brightness_error = is_bad_brightness(gray_image)
    if brightness_error:
        return None, brightness_error

    faces = FACE_DETECTOR.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60))

    real_faces = []
    for (x, y, w, h) in faces:
        face_area = gray_image[y:y + h, x:x + w]
        eyes_in_this_face = EYE_DETECTOR.detectMultiScale(face_area, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))
        if len(eyes_in_this_face) >= 1:
            real_faces.append((x, y, w, h))

    if len(real_faces) > 1:
        return None, "Multiple faces detected. Please upload a photo with only your face in frame."

    if len(real_faces) == 0:
        return rgb_image, None

    x, y, w, h = real_faces[0]
    extra_x = int(w * EXTRA_SPACE_AROUND_FACE)
    extra_y = int(h * EXTRA_SPACE_AROUND_FACE)

    left = max(0, x - extra_x)
    top = max(0, y - extra_y)
    right = min(image_as_array.shape[1], x + w + extra_x)
    bottom = min(image_as_array.shape[0], y + h + extra_y)

    cropped_image = rgb_image.crop((left, top, right, bottom))
    return cropped_image, None
