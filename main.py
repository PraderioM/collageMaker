import json
from glob import glob
from typing import List
import os

import cv2
from progressbar import progressbar

from collage import Collage
from constants import METADATA_NAME
from image_meta import ImageMeta
from input_request_tools import get_dir_path, get_img_path, get_out_path, get_integer


def get_metadata(dir_path: str) -> List[ImageMeta]:
    metadata_path = os.path.join(dir_path, METADATA_NAME)

    # Load data if already existing.
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return [ImageMeta.from_JSON(data) for data in json.load(f)]

    image_paths = glob(os.path.join(dir_path, '*'))
    print('Collecting image metadata...')
    metadata = [ImageMeta.from_path(path) for path in progressbar(image_paths)]
    metadata = [image_meta for image_meta in metadata if image_meta is not None]

    with open(metadata_path, 'w') as f:
        json.dump([img.to_JSON() for img in metadata], f)

    return metadata


def main():
    dir_path = get_dir_path()
    image_path = get_img_path()
    image = cv2.imread(image_path)
    in_h, in_w, _ = image.shape
    out_path = get_out_path('Insert path where you want to save the collage')
    n_cols = get_integer('Insert number of images you want to have on each row of the collage', 80, 2)
    n_rows = get_integer('Insert number of images you want to have on each column of the collage', 80, 2)
    out_h = get_integer(f'The input image height was {in_h} Insert output image height', in_h*4, 2)
    out_w = get_integer(f'The input image width was {in_w} Insert output image width', in_w*4, 2)
    offset = get_integer('Insert the how far away from each other can the images closest to the original be', 10, 0)
    collage = Collage.from_image(image, n_rows, n_cols, out_w, out_h)
    metadata = get_metadata(dir_path)
    collage.load_image_paths(metadata, threshold=None, offset=offset, repeat=True)
    cv2.imwrite(out_path, collage.make_collage())

if __name__ == '__main__':
    main()

