import cv2

from egg_detector.egg_detector import EggDetector


class TestEggDetector:
    def test_two_eggs(self):
        detector = EggDetector(output_dir="output")
        img = cv2.imread("test_images/two_eggs.jpg", cv2.IMREAD_COLOR)
        nesting_box_state = detector.analyze_nesting_box(img, 0)

        assert nesting_box_state.box_num == 0
        assert nesting_box_state.egg_count_blob == 2
        assert "box-0-egg-blob-detect.jpg" in nesting_box_state.egg_count_blob_img_path
        assert nesting_box_state.egg_count_yolo == 1
        assert (
            "box-0-egg_prediction-yolo.jpg" in nesting_box_state.egg_count_yolo_img_path
        )

    def test_multiple_eggs(self):
        detector = EggDetector(output_dir="output")
        img = cv2.imread("test_images/multiple_eggs.jpg", cv2.IMREAD_COLOR)
        nesting_box_state = detector.analyze_nesting_box(img, 0)

        assert nesting_box_state.egg_count_blob == 5
        assert nesting_box_state.egg_count_yolo == 0

    def test_empty_box(self):
        detector = EggDetector(output_dir="output")
        img = cv2.imread("test_images/empty_eggbox.jpg", cv2.IMREAD_COLOR)
        nesting_box_state = detector.analyze_nesting_box(img, 0)

        assert nesting_box_state.box_num == 0
        assert nesting_box_state.egg_count_blob == 0
        assert nesting_box_state.egg_count_yolo == 0
