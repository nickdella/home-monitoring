import os
from typing import List

import cv2
import numpy as np


def splice(img, regions_of_interest=None) -> List[np.ndarray]:
    """
    :param img: an opencv image
    :param regions_of_interest: a list of tuples of tuples describing the region
           bounding boxes e.g.
           [
             ((reg1_x1,reg1_y1),(reg1_x2,reg1_y2)),
             ((reg2_x1,reg2_y1),(reg2_x2,reg2_y2)),
             ...
           ]
    :return: a list of spliced images
    """
    if regions_of_interest is None:
        regions_of_interest = []

    region_images = []
    if not regions_of_interest:
        region_images = [img]
    else:
        for region in regions_of_interest:
            x1 = region[0][0]
            y1 = region[0][1]
            x2 = region[1][0]
            y2 = region[1][1]
            region_images.append(img[y1:y2, x1:x2])

    return region_images


def is_visual_debug():
    return os.environ.get("VISUAL_DEBUG")


def maybe_show_image_and_wait(img, title="Image"):
    if is_visual_debug():
        cv2.imshow(title, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cv2.waitKey(1)
