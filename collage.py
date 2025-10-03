from typing import List, Tuple, Optional, Union
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

    def make_collage(self, adjust_method: Union["N", "RGB", "SV"] = "N") -> np.array:
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
                    correction = self._image_paths[i][j][1]
                    res_img = cv2.resize(image, (w, h))

                    if adjust_method == "N":
                        pass
                    elif adjust_method == "SV":
                        hsv_img = cv2.cvtColor(res_img, cv2.COLOR_BGR2HSV)
                        hsv_img = cv2.add(hsv_img, np.reshape(np.array(correction, dtype=hsv_img.dtype), (1,1,3)))
                        res_img = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
                    elif adjust_method == "RGB":
                       res_img = cv2.add(res_img, np.reshape(np.array(correction, dtype=hsv_img.dtype), (1,1,3)))
                    else:
                        raise TypeError(f"Unrecognized adjust method '{adjust_method}'. Please choose either 'N', 'RGB' or 'SV.")

                    row.append(res_img)
                    progress.update(j*self.n_rows+i)

                row_images.append(np.concatenate(row, axis=0))

        return np.concatenate(row_images, axis=1)

    def load_image_paths(self, image_meta: List[ImageMeta], adjust_method: Union["N", "RGB", "SV"] = "N", threshold: Optional[int] = None, offset: int = 10, repeat = True):
        if len(image_meta) < self.n_cols*self.n_rows and not repeat:
            raise RuntimeError('Cannot have less images than the ones needed for the collage.s')

        pixels = [(i, j) for i in range(self.n_rows) for j in range(self.n_cols)]
        shuffle(pixels)
        self._image_paths = [['', None]*self.n_cols for _ in range(self.n_rows)]

        all_images = image_meta.copy()

        print('Finding the best images to use for the collage...')
        for i, j in progressbar(pixels):
            b, g, r = self._image[i][j]
            image_index, correction = self.get_best_match(all_images, (r, g, b), adjust_method=adjust_method, threshold=threshold, offset=offset)
            self._image_paths[i][j] = all_images[image_index].path, correction

            if not repeat:
                all_images.pop(image_index)

    def get_best_match(self, img_list, color: Tuple[int, int, int], adjust_method: Union["N", "RGB", "SV"] = "N", threshold: Optional[int] = None, offset: int = 10) -> Tuple[int, Optional[Tuple[float, float, float]]]:
        min_dist: Optional[Union[int, float]] = None
        good_matches: List[Tuple[int, float, Optional[Tuple[float, float, float]]]] = []

        for i, img in enumerate(img_list):
            if adjust_method == "N":
                dist = self.get_rgb_dist(img.means, color)
                correction = None
            elif adjust_method == "RGB":
                dist, correction = self.get_adjusted_rgb_dist(img.means, color)
            elif adjust_method == "SV":
                dist, correction = self.get_adjusted_hsv_dist(img.means, color)
            else:
                raise TypeError(f"Unrecognized adjust method '{adjust_method}'. Please choose either 'N', 'RGB' or 'SV.")

            if min_dist is None:
                min_dist = dist
                good_matches = [(i, dist, correction)]
            elif dist < min_dist:
                min_dist = dist
                good_matches = [(i, dist, correction)] + [(index, d, c) for index, d, c in good_matches if d - dist < offset]
            elif dist - min_dist < offset:
                good_matches.append((i, dist, correction))

        if threshold is not None and min_dist > threshold:
            raise RuntimeError('Unable to satisfy the proposed threshold.')

        good_match = choice(good_matches)

        return good_match[0], good_match[2]

    @staticmethod
    def get_rgb_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> int:
        return max([abs(color_1[i]- color_2[i]) for i in range(3)])

    @staticmethod
    def get_adjusted_rgb_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> Tuple[int, Tuple[float, float, float]]:
        dist = Collage.get_rgb_dist(color_1, color_2)
        # noinspection PyTypeChecker
        corr: Tuple[float,float, float] = tuple([float(color_2[i]) - float(color_1[i]) for i in range(3)])
        return dist, corr

    @staticmethod
    def get_adjusted_hsv_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> Tuple[float, Tuple[float, float, float]]:
        hsv_color_1 = cv2.cvtColor(np.reshape(np.array(np.round(color_1), dtype=np.uint8), (1,1,3)), cv2.COLOR_BGR2HSV)
        hsv_color_2 = cv2.cvtColor(np.reshape(np.array(np.round(color_2), dtype=np.uint8), (1,1,3)), cv2.COLOR_BGR2HSV)
        s_corr = float(hsv_color_2[0][0][1]) - float(hsv_color_1[0][0][1])
        v_corr = float(hsv_color_2[0][0][2]) - float(hsv_color_1[0][0][2])
        return float(np.max(cv2.absdiff(hsv_color_1[:,:,0], hsv_color_2[:,:,0]))), (0, s_corr, v_corr)
