from bing_image_downloader import downloader

from input_request_tools import get_out_path, get_string, get_integer


def main():
    out_dir = get_out_path('Insert directory where you want to save the images')
    query_str = get_string('Insert query for images')
    limit = get_integer(question='Insert maximum number of images you wish to download', default=100, min_val=10)
    downloader.download(query_str,
                        limit=limit,
                        output_dir=out_dir,
                        adult_filter_off=True,
                        force_replace=False,
                        timeout=60,
                        verbose=True)
    pass

if __name__ == '__main__':
    main()
