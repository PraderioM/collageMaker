import json
from glob import glob
from typing import List
import os

import cv2
from progressbar import progressbar

from collage import Collage
from constants import METADATA_NAME
from image_meta import ImageMeta


def get_dir_path() -> str:
    while True:
        path = input('Insert path to directory with images:\n\t')

        path = os.path.abspath(path)

        if not os.path.isdir(path):
            print(f'`{path}` is not a directory. Please insert path again.')
        else:
            return path

def get_img_path() -> str:
    while True:
        path = input('Insert path to image you want to make a collage of:\n\t')

        path = os.path.abspath(path)

        if not os.path.isfile(path):
            print(f'`{path}` is not a file. Please insert path again.')
        else:
            return path


def get_out_path() -> str:
    while True:
        path = input('Insert path where you want to save the collage:\n\t')

        path = os.path.abspath(path)

        if os.path.exists(path):
            print(f'`{path}` already exists. Please insert a different path.')
        else:
            return path


def get_n_images(dimension:str, default: int = 100) -> int:
    while True:
        n = input(f'Insert number of images you want to have on each {dimension} of the collage [{default}]:\n\t')

        if len(n) == 0:
            return default

        if not n.isnumeric():
            print(f'`{n}` is not a number. Please insert number again.')
        else:
            n = int(n)
            if n <= 1:
                print(f'Please insert an integer greater or equal than 2.')
            else:
                return n

def get_metadata(dir_path: str) -> List[ImageMeta]:
    metadata_path = os.path.join(dir_path, METADATA_NAME)

    # Load data if already existing.
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return [ImageMeta.from_JSON(data) for data in json.load(f)]

    image_paths = glob(os.path.join(dir_path, '*'))
    print('Collecting image metadata...')
    metadata = [ImageMeta.from_path(path) for path in progressbar(image_paths)]

    with open(metadata_path, 'w') as f:
        json.dump([img.to_JSON() for img in metadata], f)

    return metadata


def main():
    dir_path = get_dir_path()
    image_path = get_img_path()
    out_path = get_out_path()
    n_cols = get_n_images('row')
    n_rows = get_n_images('column')
    collage = Collage.from_image(cv2.imread(image_path), n_rows, n_cols)
    metadata = get_metadata(dir_path)
    collage.load_image_paths(metadata)
    cv2.imwrite(out_path, collage.make_collage())

if __name__ == '__main__':
    main()

