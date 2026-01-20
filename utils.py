from PIL import Image

import base64
import io


def save_image_from_base64(image_base64, filename, resize_coefficient=1):
    formatted_base64 = image_base64.split(",")[-1]

    image = Image.open(
        io.BytesIO(
            base64.b64decode(formatted_base64, validate=True)
        )
    )

    if resize_coefficient != 1:
        original_width, original_height = image.size
        image = image.resize((original_width * resize_coefficient, original_width * resize_coefficient))

    image.save(filename)

