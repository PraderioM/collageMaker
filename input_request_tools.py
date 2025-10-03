import os
from typing import List, Optional



def get_string(question: str, allowed_answers: Optional[List[str]] = None) -> str:
    if allowed_answers is not None:
        question = question + ": [ " + " | ".join(allowed_answers) + " ]\n\t"
    else:
        question = question + ":\n\t"

    a = input(question)

    while allowed_answers is not None and a not in allowed_answers:
        a = input("I did not understand your answer, please reply with one of the following: " + " | ".join(allowed_answers) + "\n\t")

    return a

def get_adjust_method():
    return get_string("""What method should be used for adjusting the color of the images used in the collage?
    "N": No adjustment made (only recommended if a huge number of images is available).
    "RGB": Images used in the collage will be uniformly added an average RGB color in order to match the target.
    "SV": Distances will be computed using solely using hue and saturation and brightness of images will be adjusted in order to match the target""",
                      ["N", "SV", "RGB"])


def get_dir_path() -> str:
    while True:
        path = input('Insert path to directory with images:\n\t')

        path = os.path.abspath(path)

        if not os.path.isdir(path):
            print(f'`{path}` is not a directory. Please insert path again.')
        else:
            return path


def get_file_path(query: str) -> str:
    while True:
        path = input(f'{query}:\n\t')

        path = os.path.abspath(path)

        if not os.path.isfile(path):
            print(f'`{path}` is not a file. Please insert path again.')
        else:
            return path


def get_out_path(question: str, allow_duplicate: bool = False) -> str:
    while True:
        path = input(question + ':\n\t')

        path = os.path.abspath(path)

        if os.path.exists(path) and not allow_duplicate:
            print(f'`{path}` already exists. Please insert a different path.')
        else:
            return path


def get_float(question:str, default: float = 100, min_val: float = 2) -> float:
    while True:
        n = input(f'{question} [{default}]:\n\t')

        if len(n) == 0:
            return default

        if not n.isnumeric():
            print(f'`{n}` is not a number. Please insert number again.')
        else:
            n = float(n)
            if n < min_val:
                print(f'Please insert a number greater or equal than {min_val}.')
            else:
                return n


def get_integer(question:str, default: int = 100, min_val: int = 2) -> int:
    while True:
        n = input(f'{question} [{default}]:\n\t')

        if len(n) == 0:
            return default

        if not n.isnumeric():
            print(f'`{n}` is not a number. Please insert number again.')
        else:
            n = int(n)
            if n < min_val:
                print(f'Please insert a number greater or equal than {min_val}.')
            else:
                return n
