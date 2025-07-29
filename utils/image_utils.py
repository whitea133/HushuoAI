import base64
import cv2
from typing import Tuple

def B64enc_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def resize(image, max_wh: Tuple[int, int] = (640, 480)):
    h, w = image.shape[:2]
    scale = min(max_wh[0] / w, max_wh[1] / h)
    if scale >= 1:
        return image
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h))

def image_to_base64(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    img = resize(img)
    _, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf).decode()