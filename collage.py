from typing import List, Tuple, Optional
from random import shuffle, choice

import cv2
import numpy as np
from progressbar import progressbar, ProgressBar

from image_meta import ImageMeta


class Collage:
    def __init__(self, image: np.array, shape: Tuple[int, int], image_paths: Optional[List[List[Tuple[str, Optional[float], Optional[float]]]]] = None):
        self._image = image
        self.shape = shape

        self._image_paths: List[List[Tuple[str, Optional[float], Optional[float]]]] = image_paths

    @classmethod
    def from_image(cls, image:np.array, n_cols: int, n_rows: int, out_w: int, out_h: int):
        return cls(cv2.resize(image, (n_cols, n_rows)), shape=(out_h, out_w))

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
                    image = cv2.imread(self._image_paths[i][j][0])
                    saturation_offset = self._image_paths[i][j][1]
                    brightness_offset = self._image_paths[i][j][2]
                    res_img = cv2.resize(image, (w, h))

                    if brightness_offset is not None:
                        hsv_img = cv2.cvtColor(res_img, cv2.COLOR_BGR2HSV)
                        hsv_img[:,:,1] = cv2.add(hsv_img[:,:,1], np.full((h,w), saturation_offset, hsv_img.dtype))
                        hsv_img[:,:,2] = cv2.add(hsv_img[:,:,2], np.full((h,w), brightness_offset, hsv_img.dtype))
                        res_img = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

                    row.append(res_img)
                    progress.update(j*self.n_rows+i)

                row_images.append(np.concatenate(row, axis=0))

        return np.concatenate(row_images, axis=1)

    def load_image_paths(self, image_meta: List[ImageMeta], sb_threshold: Optional[int] = None, threshold: Optional[int] = None, offset: int = 10, repeat = True):
        if len(image_meta) < self.n_cols*self.n_rows and not repeat:
            raise RuntimeError('Cannot have less images than the ones needed for the collage.s')

        pixels = [(i, j) for i in range(self.n_rows) for j in range(self.n_cols)]
        shuffle(pixels)
        self._image_paths = [['']*self.n_cols for _ in range(self.n_rows)]

        all_images = image_meta.copy()

        print('Finding the best images to use for the collage...')
        for i, j in progressbar(pixels):
            b, g, r = self._image[i][j]
            image_index, sat_correction, br_correction = self.get_best_match(all_images, (r, g, b), sb_threshold=sb_threshold, threshold=threshold, offset=offset)
            self._image_paths[i][j] = all_images[image_index].path, sat_correction, br_correction

            if not repeat:
                all_images.pop(image_index)

    def get_best_match(self, img_list, color: Tuple[int, int, int], sb_threshold: Optional[int] = None, threshold: Optional[int] = None, offset: int = 10) -> Tuple[int, Optional[float], Optional[float]]:
        min_dist: Optional[int | float] = None
        good_matches: List[Tuple[int, int]] = []
        sat_correction = None
        br_correction = None

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
        good_match = choice(good_matches)[1]

        if sb_threshold is not None and min_dist > sb_threshold:

            min_dist: Optional[int] = None
            good_br_corr_matches: List[Tuple[float, float, float, int]] = []

            for i, img in enumerate(img_list):
                dist, sat_offset, br_offset = self.get_hsv_brightness_corrected_dist(img.means, color)

                if min_dist is None:
                    min_dist = dist
                    good_br_corr_matches = [(dist, sat_offset, br_offset, i)]
                elif dist < min_dist:
                    min_dist = dist
                    good_br_corr_matches = [(dist, sat_offset, br_offset, i)] + [(d, s_off, b_off, index) for d, s_off, b_off, index in good_br_corr_matches if d - dist < offset]
                elif dist - min_dist < offset:
                    good_br_corr_matches.append((dist, sat_offset, br_offset, i))

            sat_correction, br_correction, good_match = choice(good_br_corr_matches)[1:]

        if threshold is not None and min_dist > threshold:
            raise RuntimeError('Unable to satisfy the proposed threshold.')

        return good_match, sat_correction, br_correction

    @staticmethod
    def get_color_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> int:
        return max([abs(color_1[i]- color_2[i]) for i in range(3)])

    @staticmethod
    def get_hsv_brightness_corrected_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> Tuple[float, float, float]:
        hsv_color_1 = cv2.cvtColor(np.reshape(np.array(np.round(color_1), dtype=np.uint8), (1,1,3)), cv2.COLOR_BGR2HSV)
        hsv_color_2 = cv2.cvtColor(np.reshape(np.array(np.round(color_2), dtype=np.uint8), (1,1,3)), cv2.COLOR_BGR2HSV)
        sat_diff = float(hsv_color_1[0][0][1]) - float(hsv_color_2[0][0][1])
        br_diff = float(hsv_color_1[0][0][2]) - float(hsv_color_2[0][0][2])
        return float(np.max(cv2.absdiff(hsv_color_1[:,:,0], hsv_color_2[:,:,0]))), sat_diff, br_diff
