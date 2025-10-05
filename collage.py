from typing import List, Tuple, Optional, Union
from random import shuffle, choice

import cv2
import numpy as np
from progressbar import progressbar, ProgressBar

from image_meta import ImageMeta

ADJUSTMENT_METHOD = Union["N", "RGB", "SV", "V"]

class Collage:
    def __init__(self, image: np.array, shape: Tuple[int, int], image_paths: Optional[List[List[str]]] = None):
        self._image = image
        self.shape = shape

        self._image_paths: List[List[str]] = image_paths

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

    def make_collage(self, adjust_method: ADJUSTMENT_METHOD = "N") -> np.array:
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
                    res_img = cv2.resize(image, (w, h))

                    row.append(res_img)
                    progress.update(j*self.n_rows+i)

                row_images.append(np.concatenate(row, axis=0))

        out_img = np.concatenate(row_images, axis=1)

        # Apply correction to resulting collage
        if adjust_method == "N":
            pass
        elif adjust_method == "RGB":
            out_img = self.apply_rgb_correction(out_img)
        elif adjust_method == "V":
            out_img = self.apply_hsv_correction(out_img, [0,1])
        elif adjust_method == "SV":
            out_img = self.apply_hsv_correction(out_img, [0])
        else:
            raise TypeError(
                f"Unrecognized adjust method '{adjust_method}'. Please choose either 'N', 'RGB' or 'SV.")

        return out_img

    def load_image_paths(self, image_meta: List[ImageMeta], adjust_method: ADJUSTMENT_METHOD = "N", threshold: Optional[int] = None, offset: int = 10, repeat = True):
        if len(image_meta) < self.n_cols*self.n_rows and not repeat:
            raise RuntimeError('Cannot have less images than the ones needed for the collage.s')

        pixels = [(i, j) for i in range(self.n_rows) for j in range(self.n_cols)]
        shuffle(pixels)
        self._image_paths = [['', None]*self.n_cols for _ in range(self.n_rows)]

        all_images = image_meta.copy()

        print('Finding the best images to use for the collage...')
        for i, j in progressbar(pixels):
            b, g, r = self._image[i][j]
            image_index = self.get_best_match(all_images, (r, g, b), adjust_method=adjust_method, threshold=threshold, offset=offset)
            self._image_paths[i][j] = all_images[image_index].path

            if not repeat:
                all_images.pop(image_index)

    def get_best_match(self, img_list, color: Tuple[int, int, int], adjust_method: ADJUSTMENT_METHOD = "N", threshold: Optional[int] = None, offset: int = 10) -> int:
        min_dist: Optional[Union[int, float]] = None
        good_matches: List[Tuple[int, float]] = []

        for i, img in enumerate(img_list):
            if adjust_method == "N":
                dist = self.get_rgb_dist(img.means, color)
            elif adjust_method == "RGB":
                dist = self.get_rgb_dist(img.means, color)
            elif adjust_method == "SV":
                dist = self.get_hsv_dist(img.means, color, excluded_channels=[1,2])
            elif adjust_method == "V":
                dist = self.get_hsv_dist(img.means, color, excluded_channels=[2])
            else:
                raise TypeError(f"Unrecognized adjust method '{adjust_method}'. Please choose either 'N', 'RGB' or 'SV.")

            if min_dist is None:
                min_dist = dist
                good_matches = [(i, dist)]
            elif dist < min_dist:
                min_dist = dist
                good_matches = [(i, dist)] + [(index, d) for index, d in good_matches if d - dist < offset]
            elif dist - min_dist < offset:
                good_matches.append((i, dist))

        if threshold is not None and min_dist > threshold:
            raise RuntimeError('Unable to satisfy the proposed threshold.')

        good_match = choice(good_matches)

        return good_match[0]

    @staticmethod
    def get_rgb_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int]) -> int:
        # WARNING colors are in RGB format unlike the usual BGR of cv2.
        return max([abs(color_1[i]- color_2[i]) for i in range(3)])

    @staticmethod
    def get_hsv_dist(color_1: Tuple[int, int, int], color_2: Tuple[int, int, int], excluded_channels: Optional[List[Union[0,1,2]]] = None) -> float:
        # WARNING colors are in RGB format unlike the usual BGR of cv2.
        r1, g1, b1 = color_1
        r2, g2, b2 = color_2
        hsv_color_1 = cv2.cvtColor(np.reshape(np.array(np.round((b1, g1, r1)), dtype=np.uint8), (1,1,3)), cv2.COLOR_RGB2HSV)
        hsv_color_2 = cv2.cvtColor(np.reshape(np.array(np.round((b2, g2, r2)), dtype=np.uint8), (1,1,3)), cv2.COLOR_RGB2HSV)

        dist = 0
        for channel in range(3):
            if excluded_channels is not None and channel not in excluded_channels:
                dist += float(np.max(cv2.absdiff(hsv_color_1[:,:,channel], hsv_color_2[:,:,channel])))
        return dist

    def apply_hsv_correction(self, img, non_corrected_channels: Optional[List[Union[0,1,2]]] = None):
        # Pixelate the image so that each pixel matches a pixel of self._image. then convert it to HSV.
        # I do not dare to make this conversion on the small image as it might play badly with the HSV to BGR conversion on resizing.
        o_h, o_w, _ = img.shape
        pixelated_img = cv2.resize(cv2.resize(img, (self.n_cols, self.n_rows)), (o_w, o_h))
        pixelated_hsv = cv2.cvtColor(pixelated_img, cv2.COLOR_BGR2HSV)

        # self._image should be used as a model on where to add and subtract values in order to make the given img look like it.
        mask = cv2.resize(self._image, (o_w, o_h))
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2HSV)

        # We avoid applying any correction on the specified channels.
        if non_corrected_channels is not None:
            for channel in set(non_corrected_channels):
                pixelated_hsv[:, :, channel] = 0
                mask[:, :, channel] = 0

        # We apply the mask in 2 steps, considering the values that need to be added and those that need subtraction
        subtract_mask = np.maximum(pixelated_hsv, mask) - mask
        add_mask = mask - np.minimum(pixelated_hsv, mask)

        # We apply both masks to the given image. We need to apply them in hsv format.
        out_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        out_hsv = cv2.add(out_hsv, add_mask)
        out_hsv = cv2.subtract(out_hsv, subtract_mask)

        # We go back to BGR format and return.
        return cv2.cvtColor(out_hsv, cv2.COLOR_HSV2BGR)

    def apply_rgb_correction(self, img):
        # resize the image to match the size of self._image. This is used to create the mask.
        pixelated = cv2.resize(img, (self.n_cols, self.n_rows))

        # We apply the mask in 2 steps, considering the values that need to be added and those that need substraction
        h, w, _ = img.shape
        add_mask = np.maximum(pixelated, self._image) - pixelated
        add_mask = cv2.resize(add_mask, (h, w))
        subtract_mask = pixelated - np.minimum(self._image, pixelated)
        subtract_mask = cv2.resize(subtract_mask, (h, w))

        # We apply both masks to the given image.
        out_img = cv2.add(img, add_mask)
        out_img = cv2.subtract(out_img, subtract_mask)

        # We go back to BGR format and return.
        return out_img
