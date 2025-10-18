from typing import List, Tuple
from glob import glob
import os

from PIL import Image
import imagehash
from progressbar import progressbar

from input_request_tools import get_dir_path, get_string

def main():
    dir_path = get_dir_path()
    n_removed_duplicates = 0
    if get_string(f"All images in {dir_path}  and subdirectories that have the same hash will be removed leaving only one copy (with the most resolution). Do you wish to proceed?", ["y", "n"]) == "y":
        image_paths = glob(os.path.join(dir_path, '**'), recursive=True)
        hashes = []
        img_meta: List[Tuple[str, int]] = []
        for new_path in progressbar(image_paths):
            try:
                new_img = Image.open(new_path)
            except:
                continue

            w, h = new_img.size
            new_res = w * h
            try:
                new_hash = imagehash.average_hash(new_img)
            except OSError:
                continue

            try:
                prev_hash_index = hashes.index(new_hash)
                prev_path, prev_res = img_meta[prev_hash_index]
                if prev_res >= new_res:
                    os.remove(new_path)
                else:
                    os.remove(prev_path)
                    img_meta[prev_hash_index] = (new_path, new_res)
                    hashes[prev_hash_index] = new_hash

                n_removed_duplicates += 1
            except ValueError:
                hashes.append(new_hash)
                img_meta.append((new_path, new_res))

        print(f"Successfully removed {n_removed_duplicates} duplicate images.")
    else:
        print("Exiting program.")


if __name__ == "__main__":
    main()
