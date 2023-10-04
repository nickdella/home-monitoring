from collections import defaultdict
import dataclasses
from dataclasses import dataclass, field
import json
import os
from typing import Optional

import arrow
import cv2
import numpy as np
from ultralytics import YOLO

from egg_detector import logger, utils

logger = logger.get(__name__)


@dataclass
class NestingBoxState:
    box_num: int
    ts: int
    chicken_count_yolo: Optional[int] = 0
    egg_count_blob: Optional[int] = 0
    egg_count_blob_img_path: Optional[str] = None
    egg_count_yolo: Optional[int] = 0
    egg_count_yolo_img_path: Optional[str] = None
    yolo_unknown_egg_objects: dict[int, int] = field(default_factory=lambda: {})
    yolo_unknown_chicken_objects: dict[int, int] = field(default_factory=lambda: {})


class EggDetector:
    def __init__(self, output_dir):
        self.dt = arrow.now()
        self.output_file_dir = os.path.join(
            output_dir, self.dt.format("YYYY-MM-DD-HH-mm-ss")
        )
        os.makedirs(self.output_file_dir)
        self.box_num = None

    def analyze_nesting_box(self, img, box_num):
        self.box_num = box_num
        num_eggs_blob, blob_img_path = self._count_eggs_blob(img)
        num_eggs_yolo, unknown_egg_objects, yolo_img_path = self._count_eggs_yolo(img)
        num_chickens, unknown_chicken_objects, img_path = self._detect_chicken(img)
        state = NestingBoxState(
            box_num=box_num,
            ts=self.dt.int_timestamp,
            chicken_count_yolo=num_chickens,
            egg_count_blob=num_eggs_blob,
            egg_count_blob_img_path=blob_img_path,
            egg_count_yolo=num_eggs_yolo,
            egg_count_yolo_img_path=yolo_img_path,
            yolo_unknown_egg_objects=unknown_egg_objects,
            yolo_unknown_chicken_objects=unknown_chicken_objects,
        )
        results_filename = os.path.join(
            self.output_file_dir, f"box-{box_num}-results.json"
        )
        with open(results_filename, "w") as f:
            f.write(json.dumps(dataclasses.asdict(state), indent=2))

        return state

    def _count_eggs_blob(self, img) -> (int, str):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        utils.maybe_show_image_and_wait(img)

        # This image processing sequence aims isolate the eggs from the noisy nesting
        # box background (wood shavings). The current implementation applies a mix of
        # thresholding and blurring before running a blob detector that finds fairly
        # large, somewhat circular objects.
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        utils.maybe_show_image_and_wait(img)

        img = cv2.GaussianBlur(img, (23, 23), 0)
        utils.maybe_show_image_and_wait(img)

        threshold, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        utils.maybe_show_image_and_wait(img)

        img = cv2.bitwise_not(img)
        utils.maybe_show_image_and_wait(img)

        return self._detect_egg_blobs(img)

    def _detect_egg_blobs(self, img, min=10, max=200):
        # TODO Test at different times of day, see if thresholds need to be adjusted
        params = cv2.SimpleBlobDetector_Params()
        params.minThreshold = min
        params.maxThreshold = max
        params.filterByCircularity = True
        params.minCircularity = 0.5
        params.filterByArea = True
        params.minArea = 2000
        params.maxArea = 10000
        params.filterByConvexity = False
        # params.minConvexity = 0.2
        params.filterByInertia = False
        # params.minInertiaRatio = 0.1
        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(img)
        for kp in keypoints:
            logger.info(
                f"Detected egg blob at ({kp.pt[0]},{kp.pt[1]}) of size {kp.size}"
            )

        # This is just for testing/visualizing
        img_with_keypoints = cv2.drawKeypoints(
            img,
            keypoints,
            np.array([]),
            (0, 0, 255),
            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )
        utils.maybe_show_image_and_wait(img_with_keypoints)
        filename = os.path.join(
            self.output_file_dir, f"box-{self.box_num}-egg-blob-detect.jpg"
        )
        cv2.imwrite(filename, img_with_keypoints)

        return len(keypoints), filename

    def _count_eggs_yolo(self, img):
        return self._count_objects_yolo(
            img,
            project="egg_prediction",
            confidence=0.03,
            iou=0.8,
            valid_classes=["apple", "sports ball", "orange"],
            # TODO toilet, bowl, sink + refactor to share between methods
            ignored_classes=["bench", "chair", "bird"],
        )

    def _detect_chicken(self, img) -> (bool, dict[str, int], str):
        return self._count_objects_yolo(
            img,
            project="chicken_prediction",
            confidence=0.03,
            iou=0.7,
            valid_classes=["bird", "bear", "dog", "cat", "elephant"],
            ignored_classes=["bench", "chair", "apple", "sports ball", "orange"],
        )

    def _count_objects_yolo(
        self, img, project, confidence, iou, valid_classes, ignored_classes
    ) -> (int, dict[str, int], str):
        logger.info(f"Running YOLO predict for {project}")
        valid_object_count = 0
        unknown_object_counts = defaultdict(lambda: 0)

        model = YOLO("models/yolov8l.pt")
        result = model.predict(
            img, save=True, conf=confidence, project=project, agnostic_nms=True
        )[0]
        for box in result.boxes:
            class_name = result.names[int(box.cls)]
            result_conf = float(box.conf)
            logger.info(f"Detected class {class_name} with conf={result_conf}")
            if class_name in valid_classes:
                # TODO we're getting overlapping boxes of different classes
                # Seems like we need to set multi_label=False in non_max_suppression,
                # but this doesn't look configurable?
                valid_object_count += 1
            elif class_name not in ignored_classes:
                unknown_object_counts[class_name] += 1

        # TODO Don't overwrite the log file
        img_path = f"{result.save_dir}/{result.path}"
        img = cv2.imread(img_path)
        filename = os.path.join(
            self.output_file_dir, f"box-{self.box_num}-{project}-yolo.jpg"
        )
        cv2.imwrite(filename, img)
        utils.maybe_show_image_and_wait(img)

        return valid_object_count, dict(unknown_object_counts), filename


# for local testing/debugging. Just create a virtual env,
# export VISUAL_DEBUG=True and run this module
if __name__ == "__main__":
    detector = EggDetector()
    input_img = cv2.imread("images/7_eggs.jpg")
    # input_img = cv2.imread("images/bard_rock_side.jpg")
    res = detector.analyze_nesting_box(input_img)
    logger.info(res)
