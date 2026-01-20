import hashlib
import os
import random
import shutil

from process import process_blocks
from utils import save_image_from_base64
from flask import Flask, request, jsonify


app = Flask(__name__)


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


def generate_random_name():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(15))


def get_string_hash(s):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(s.encode("utf-8"))

    return sha256_hash.hexdigest()


def process_data(sample):
    shutil.rmtree('./pictures')
    os.mkdir('./pictures')

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
