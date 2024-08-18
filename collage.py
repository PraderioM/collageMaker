from typing import List, Tuple, Optional
from random import shuffle, choice

import cv2
import numpy as np
from progressbar import progressbar, ProgressBar

from image_meta import ImageMeta


class Collage:
    def __init__(self, image: np.array, shape: Tuple[int, int], image_paths: Optional[List[List[str]]] = None):
        self._image = image
        self.shape = shape

        self._image_paths = image_paths

    @classmethod
    def from_image(cls, image:np.array, n_cols: int, n_rows: int):
        h, w, _ = image.shape
        return cls(cv2.resize(image, (n_cols, n_rows)), shape=(h, w))

    @property
    def n_rows(self):
        n_rows, _, _ = self._image.shape
        return n_rows

    @property
    def n_cols(self):
        _, n_cols, _ = self._image.shape
        return n_cols

    @property
    def images_height(self):
        return int(self.shape[0] / self.n_rows)

    @property
    def images_width(self):
        return int(self.shape[1] / self.n_cols)

    def make_collage(self) -> np.array:
        if self._image_paths is None:
            raise RuntimeError('Cannot make the collage before loading the images.')

        h, w = self.images_height, self.images_width

        row_images: List[np.ndarray] = []

        print('Creating collage...')
        with ProgressBar(max_value=self.n_rows*self.n_cols) as progress:
            for j in range(self.n_cols):
                row: List[np.array] = []
                for i in range(self.n_rows):
                    image = cv2.imread(self._image_paths[i][j])

                    row.append(cv2.resize(image, (w, h)))
                    progress.update(j*self.n_rows+i)

                row_images.append(np.concatenate(row, axis=0))

        return np.concatenate(row_images, axis=1)

    def load_image_paths(self, image_meta: List[ImageMeta], threshold: Optional[int] = None, offset: int = 10, repeat = True):
        if len(image_meta) < self.n_cols*self.n_rows and not repeat:
            raise RuntimeError('Cannot have less images than the ones needed for the collage.s')

        pixels = [(i, j) for i in range(self.n_rows) for j in range(self.n_cols)]
        shuffle(pixels)
        self._image_paths = [['']*self.n_cols for _ in range(self.n_rows)]

        all_images = image_meta.copy()

        print('Finding the best images to use for the collage...')
        for i, j in progressbar(pixels):
            b, g, r = self._image[i][j]
            image_index = self.get_best_match(all_images, (r, g, b), threshold=threshold, offset=offset)
            self._image_paths[i][j] = all_images[image_index].path

            if not repeat:
                all_images.pop(image_index)

    def get_best_match(self, img_list, color: Tuple[int, int, int], threshold: Optional[int] = None, offset: int = 10) -> int:
        min_dist: Optional[int] = None
        good_matches: List[Tuple[int, int]] = []

        for i, img in enumerate(img_list):
            dist = self.get_color_dist(img.means, color)

            if min_dist is None:
                min_dist = dist
                good_matches = [(dist, i)]
            elif dist < min_dist:
                min_dist = dist
                good_matches = [(dist, i)] + [(d, index) for d, index in good_matches if d - dist < offset]
            elif dist - min_dist < offset:
                good_matches.append((dist, i))

        if threshold is not None and min_dist > threshold:
            raise RuntimeError('Unable to satisfy the proposed threshold.')

        return choice(good_matches)[1]

    @staticmethod
    def get_color_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> int:
        return max([abs(color_1[i]- color_2[i]) for i in range(3)])
