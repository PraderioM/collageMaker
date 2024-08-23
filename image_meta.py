from typing import Tuple

import cv2


class ImageMeta:
    def __init__(self, path: str, shape: Tuple[int, int], means: Tuple[int, int, int]):
        self.path = path
        self.shape = shape
        self.means = means

    @classmethod
    def from_path(cls, path: str):

        image = cv2.imread(path)
        if image is None:
            print(f'could not read image {path}. It will be skipped.')
            return None

        h, w, _ = image.shape

        # Images are loaded in bgr format.
        b, g, r = image[:, :, 0].mean(), image[:, :, 1].mean(), image[:, :, 2].mean()

        return cls(path=path, shape=(h, w), means=(r, g, b))

    @classmethod
    def from_JSON(cls, data):
        return cls(data['path'], data['shape'], data['means'])

    def to_JSON(self):
        return {
            'path': self.path,
            'shape': self.shape,
            'means': self.means
        }

    @property
    def height(self):
        return self.shape[0]

    @property
    def width(self):
        return self.shape[1]

    @property
    def mean_red(self):
        return self.means[0]

    @property
    def mean_green(self):
        return self.means[1]

    @property
    def mean_blue(self):
        return self.means[2]