from ultralytics import YOLO


model = YOLO("yolov8x.pt")


MODEL_NAMING_TRANSLATE = {
    "sheep": "horse",
    "boat": "ship",
    "sports ball": "ball"
}


OBJECTS_LIST = [
    "basketball",
    "bicycle",
    "car",
    "cat",
    "couch",
    "dog",
    "horse",
    "ship",
    "train"
]


def process_predict_results(predict_results):
    processed_predict_results = [None for _ in range(6)]
    used_obj = set()

    for i, block_results in enumerate(predict_results):
        s = set()

        for result in block_results:
            if result["name"] in OBJECTS_LIST:
                s.add(result["name"])

        if len(s) == 1:
            name = s.pop()

            processed_predict_results[i] = name
            used_obj.add(name)

    for i, block_results in enumerate(predict_results):
        if processed_predict_results[i]:
            continue

        # block_results.sort(key=lambda x: x["conf"], reverse=True)
        for result in block_results:
            if result["name"] not in used_obj and result["name"] in OBJECTS_LIST:
                result[i] = result["name"]
                used_obj.add(result["name"])

    return processed_predict_results


def predict_blocks(images):
    predict_results = list()

    for image in images:
        if not image:
            predict_results.append(list())
            continue

        predict = model.predict(image)[0]

        block_results = list()

        # print(f"Image {image}")

        for box in predict.boxes:
            class_id = predict.names[box.cls[0].item()]

            if class_id in MODEL_NAMING_TRANSLATE:
                class_id = MODEL_NAMING_TRANSLATE[class_id]

            cords = box.xyxy[0].tolist()
            cords = [round(x) for x in cords]
            conf = round(box.conf[0].item(), 2)

            block_results.append({
                "image": image,
                "name": class_id,
                "conf": conf
            })

            # print(class_id, cords, conf)

        predict_results.append(block_results)

        # print("-----------------")

    # print(json.dumps(predict_results, indent=2))
    return predict_results


def process_blocks(images):
    predict_results = predict_blocks(images)
    # print(predict_results)

    processed_predict_results = process_predict_results(predict_results)
    # print(processed_predict_results)

    return processed_predict_results
