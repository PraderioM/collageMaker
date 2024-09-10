import os



def get_string(question: str) -> str:
    return input(question + ':\n\t')


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


def get_out_path(question: str) -> str:
    while True:
        path = input(question + ':\n\t')

        path = os.path.abspath(path)

        if os.path.exists(path):
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
