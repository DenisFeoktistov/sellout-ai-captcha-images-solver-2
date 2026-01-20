import json
import hashlib

from main import process_blocks
from utils import save_image_from_base64

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


def main():
    with open("pictures.json") as pictures_file:
        data = json.loads(pictures_file.read())

    blocks_to_process = list()
    for i, sample in enumerate(data):
        save_image_from_base64(sample["data"]["bgImage"], f"{BASE_IMAGE_DIR}/{i + 1}_bgImage.png")
        save_image_from_base64(sample["data"]["image"], f"{BASE_IMAGE_DIR}/{i + 1}_image.png")

        captcha_list = list()
        for j, image in enumerate(sample["data"]["bgList"]):
            if image.startswith("data"):
                block_name = f"{BASE_IMAGE_DIR}/{i + 1}_{j + 1}_bgList.png"

                captcha_list.append(block_name)
                save_image_from_base64(image, block_name)
            else:
                captcha_list.append(None)

        blocks_to_process.append(captcha_list)

    for captcha_list in blocks_to_process:
        # print(captcha_list)
        process_blocks(captcha_list)
        break


def tasks_test():
    with open("texts.txt") as tasks_file:
        tasks = tasks_file.read().strip().split("\n")

    for i, row in enumerate(tasks):
        name = f"pictures/tasks_{i}.png"
        base64_image = row.split()[1].split(",")[-1]

        string = row.split()[1]
        sha256_hash = hashlib.sha256()
        sha256_hash.update(string.encode("utf-8"))

        save_image_from_base64(base64_image, name)
        print(f"Hash {row.split()[0]}: {name}")
        print(f"Calculated hash: {sha256_hash.hexdigest()}")
        print()


if __name__ == "__main__":
    main()
    # tasks_test()
