import base64
import hashlib
import os
import random
import shutil
from contextlib import suppress

import pytesseract
from PIL import Image
from flask import Flask, request, jsonify
from ultralytics import YOLO

from process import process_blocks
from utils import save_image_from_base64


app = Flask(__name__)
click_captcha_model = YOLO("yolov8x.pt")


BASE_IMAGE_DIR = "pictures"
TASKS_HASH_DICT = {
    "2bf11bf9b2eb332608299983efbc92610e5359b0997df6292518df061ca290b9": "bicycle",
    "2ea108720ebc70857e23391b5aef933369d0ae608ace6465d344e56f26f3c32e": "ball",
    "306ebdc5672965bd31597597ddd67cdc2110a895ea16356050a1b122bed68375": "ship",
    "41bce9bbe539552cf56ebbb3fe6a8223718206fad2a9f7c2885c40fef9b888f2": "horse",
    "42ae13a78935be55919ec6c54be4e09d79cc709d9b0b82df22754f0b3f27c00d": "car",
    "6aed78ba50749c4fa5ddc939b733f5351938ca27fee4c06d72f0b74434a4f34b": "cat",
    "a7e2c731b72cc41cbf24721a79c501236b882c70761aafc1d15778e5b0446f9c": "train",
    "b2ce4a42de22b08649333f21dc44a15ebd7f990b3f32c945191693f4c27b7ae3": "dog",
    "9f5de0c7edb5944ee32f86acc41ced9b750e3c32eee3406999133d0e6fd2a7ed": "coach",
}

TASK_D = {
    "背包": "backpack",
    "狗": "dog",
    "火车": "train",
    "自行车": "bicycle",
    "汽车": "car",
    "猫": "cat",
    "沙发": "couch",
    "马": "horse",
    "船": "ship",
    "球": "sports ball",
}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


def ensure_pictures_dir():
    os.makedirs(BASE_IMAGE_DIR, exist_ok=True)


def generate_random_name():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(15))


def get_string_hash(s):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(s.encode("utf-8"))

    return sha256_hash.hexdigest()


def process_data(sample):
    if os.path.exists(f'./{BASE_IMAGE_DIR}'):
        shutil.rmtree(f'./{BASE_IMAGE_DIR}')
    os.mkdir(f'./{BASE_IMAGE_DIR}')

    start_block = None
    finish_block = None

    task_hash = get_string_hash(sample["data"]["image"])

    task = random.choice(list(TASKS_HASH_DICT.values()))
    if task_hash in TASKS_HASH_DICT:
        task = TASKS_HASH_DICT[get_string_hash(sample["data"]["image"])]

    # print(f"Task: {task}")

    captcha_list = list()
    for i, image in enumerate(sample["data"]["bgList"]):
        if image.startswith("data"):
            block_name = f"{BASE_IMAGE_DIR}/{generate_random_name()}.png"

            captcha_list.append(block_name)
            save_image_from_base64(image, block_name)
        else:
            captcha_list.append(None)
            finish_block = i

    result = process_blocks(captcha_list)

    for i, obj in enumerate(result):
        if not obj and i != finish_block:
            start_block = i

        if obj == task:
            start_block = i
            break

    return start_block, finish_block


def get_image_size(image_path):
    image = Image.open(image_path)
    return image.size


def get_cell(image_size, cord):
    i = cord[1] // (image_size[1] // 2)
    j = cord[0] // (image_size[0] // 3)
    return i, j


def to_normal_list(s):
    return " ".join((" ".join(s.split(',')).split("，"))).split()


def generate_random_point_in_rectangle(x1, y1, x2, y2):
    x_delta = x2 - x1
    y_delta = y2 - y1
    random_x = random.randint(x1 + x_delta // 3, x2 - x_delta // 3)
    random_y = random.randint(y1 + y_delta // 3, y2 - y_delta // 3)
    return random_x, random_y


def process_click_captcha(blocks_image_path, task_image_path, size):
    custom_config = '--oem 3 --psm 6 --user-words whitelist.txt'
    task_tokens = to_normal_list(
        pytesseract.image_to_string(task_image_path, lang="chi_sim", config=custom_config)
    )
    task_labels = [TASK_D[token] for token in task_tokens if token in TASK_D]
    task_labels = task_labels + [""] * (4 - len(task_labels))

    predict = click_captcha_model.predict(blocks_image_path)[0]

    cells = [[0 for _ in range(3)] for _ in range(2)]
    class_dict = {}

    blocks_image_size = get_image_size(blocks_image_path)
    for box in predict.boxes:
        class_id = predict.names[box.cls[0].item()]
        cords = [round(x) for x in box.xyxy[0].tolist()]
        conf = round(box.conf[0].item(), 2)

        i, j = get_cell(blocks_image_size, (cords[0], cords[1]))

        class_dict.setdefault(class_id, []).append((-conf, cords, (i, j)))
        cells[i][j] = 1

    result = [0 for _ in range(len(task_labels))]
    fallback_map = {
        "backpack": "person",
        "couch": "chair",
        "dog": "teddy bear",
        "bicycle": "frisbee",
        "ship": "boat",
    }

    for k, label in enumerate(task_labels):
        if label in class_dict:
            for possible_box in sorted(class_dict[label]):
                i, j = possible_box[2]
                if cells[i][j] == 1:
                    result[k] = generate_random_point_in_rectangle(*possible_box[1])
                    cells[i][j] = 2
                    break

        fallback_label = fallback_map.get(label)
        if result[k] == 0 and fallback_label in class_dict:
            for possible_box in sorted(class_dict[fallback_label]):
                i, j = possible_box[2]
                if cells[i][j] == 1:
                    result[k] = generate_random_point_in_rectangle(*possible_box[1])
                    cells[i][j] = 2
                    break

    if not all(point != 0 for point in result):
        for k in range(len(result)):
            if result[k] != 0:
                continue

            for i in range(2):
                for j in range(3):
                    if cells[i][j] == 2:
                        continue

                    y = random.randint(
                        i * (blocks_image_size[1] // 2) + (blocks_image_size[1] // 6),
                        (i + 1) * (blocks_image_size[1] // 2) - (blocks_image_size[1] // 6)
                    )
                    x = random.randint(
                        j * (blocks_image_size[0] // 3) + (blocks_image_size[0] // 9),
                        (j + 1) * (blocks_image_size[0] // 3) - (blocks_image_size[0] // 9)
                    )
                    result[k] = (x, y)
                    cells[i][j] = 2
                    break

                if result[k] != 0:
                    break

    x_scale = size[0] / blocks_image_size[0]
    y_scale = size[1] / blocks_image_size[1]

    return [
        [int(point[0] * x_scale), int(point[1] * y_scale)]
        for point in result
        if point != 0
    ]


def process_click_captcha_request(base64_blocks_image, base64_task_image, size):
    ensure_pictures_dir()

    blocks_image_data = base64.b64decode(base64_blocks_image)
    task_image_data = base64.b64decode(base64_task_image)

    blocks_image_path = f'{generate_random_name()}.png'
    task_image_path = f'{generate_random_name()}.png'

    with open(blocks_image_path, 'wb') as f:
        f.write(blocks_image_data)

    with open(task_image_path, 'wb') as f:
        f.write(task_image_data)

    original_image = Image.open(task_image_path)
    resized_image = original_image.resize((original_image.size[0] * 2, original_image.size[1] * 2))
    resized_image.save(task_image_path)

    try:
        return process_click_captcha(blocks_image_path, task_image_path, size)
    finally:
        with suppress(FileNotFoundError):
            os.remove(blocks_image_path)
        with suppress(FileNotFoundError):
            os.remove(task_image_path)


@app.route('/captcha_images/solve_drag_images', methods=['POST'])
def solve():
    # Receive base64-encoded image from the JSON payload
    data = request.get_json()

    result = process_data(data)

    response = {
        "start_block": result[0],
        "finish_block": result[1]
    }

    return response


@app.route('/captcha_images/solve_image_captcha', methods=['POST'])
def solve_image_captcha():
    data = request.get_json()

    result = process_click_captcha_request(
        data['blocks_image'],
        data['task_image'],
        data['size']
    )

    return jsonify({"result": result})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
