import os
from glob import glob

from bing_image_downloader import downloader
from progressbar import progressbar

from input_request_tools import get_out_path, get_string, get_integer


def main():
    out_dir = get_out_path('Insert directory where you want to save the images', allow_duplicate=True)
    forbidden_names = [os.path.basename(path) for path in glob(os.path.join(out_dir, '*'))]
    query_str_list = []
    while True:
        query_str = ""
        while query_str == "" or query_str in forbidden_names or query_str in query_str_list:
            query_str = get_string('Insert query for images')
            if query_str in forbidden_names:
                print(f"Cannot use the query {query_str} as there is already a folder in {out_dir} with that name.")
            elif query_str in query_str_list:
                print(f"The query {query_str} has already been added to the list of queries.")
            pass
        query_str_list.append(query_str)
        forbidden_names.append(query_str)

        if get_string('Do you wish to add another query to the list of queries?', ["y", "n"]) == "n":
            break

    limit = get_integer(question='Insert maximum number of images you wish to download for each query', default=100, min_val=10)

    for query_str in progressbar(query_str_list):
        downloader.download(query_str,
                            limit=limit,
                            output_dir=out_dir,
                            adult_filter_off=True,
                            force_replace=False,
                            timeout=60,
                            verbose=True)


if __name__ == '__main__':
    main()
