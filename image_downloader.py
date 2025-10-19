from glob import glob
import os
import urllib.parse
import urllib.request
import urllib
import re
import imghdr
import posixpath
from typing import Optional

from progressbar import progressbar, ProgressBar

from input_request_tools import get_out_path, get_string, get_integer


def save_image(link, file_path, headers, timeout: int = 60, verbose:bool = False):
    request = urllib.request.Request(link, None, headers)
    image = urllib.request.urlopen(request, timeout=timeout).read()
    if not imghdr.what(None, image):
        if verbose:
            print('[Error]Invalid image, not saving {}\n'.format(link))
        raise ValueError('Invalid image, not saving {}\n'.format(link))
    with open(str(file_path), 'wb') as f:
        f.write(image)


def download_image(link: str, output_name: str, headers, timeout: int = 60, verbose: bool = False) -> int:
    # Get the image link
    try:
        path = urllib.parse.urlsplit(link).path
        filename = posixpath.basename(path).split('?')[0]
        file_type = filename.split(".")[-1]
        if file_type.lower() not in ["jpe", "jpeg", "jfif", "exif", "tiff", "gif", "bmp", "png", "webp", "jpg"]:
            file_type = "jpg"

        if verbose:
            # Download the image
            print(f"[%] Downloading Image from {link}")

        save_image(link, ".".join([output_name, file_type]), headers=headers, timeout=timeout)
        if verbose:
            print("[%] File Downloaded !\n")
        return 1

    except Exception as e:
        if verbose:
            print("[!] Issue getting: {}\n[!] Error:: {}".format(link, e))
        return 0


def scrap_bing(query: str, output_dir:str, limit: int = 100, no_new_downloads_page_limit: Optional[int] = 1000, verbose: bool = False):
    adult = "on"
    timeout = 60
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
      'AppleWebKit/537.11 (KHTML, like Gecko) '
      'Chrome/23.0.1271.64 Safari/537.11',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'en-US,en;q=0.8',
      'Connection': 'keep-alive'}

    pages_without_new_downloads = 0
    seen_links = set()
    bar = ProgressBar(max_value=limit)
    bar.update(0)
    download_count = 0
    page_count = 0

    while (download_count < limit) and (no_new_downloads_page_limit is None or pages_without_new_downloads < no_new_downloads_page_limit):
        if verbose:
            print(f'\n\n[!!]Indexing page: {page_count}\n')
        # Parse the page source and download pics
        request_url = 'https://www.bing.com/images/async?q=' + urllib.parse.quote_plus(query) \
                      + '&first=' + str(page_count) + '&count=' + str(limit) \
                      + '&adlt=' + adult + '&qft=' + ''
        request = urllib.request.Request(request_url, None, headers=headers)
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf8')
        if html == "":
            if verbose:
                print("[%] No more images are available")
            break
        links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)
        if verbose:
            print("[%] Indexed {} Images on Page {}.".format(len(links), page_count + 1))
            print("\n===============================================\n")

        prev_downloads = download_count
        for link in links:
            if download_count < limit and link not in seen_links:
                seen_links.add(link)
                download_count += download_image(link,
                                                 output_name=os.path.join(output_dir, f"image_{download_count}"),
                                                 headers=headers,
                                                 timeout=timeout,
                                                 verbose=verbose)
                bar.update(download_count)

        page_count += 1
        if verbose:
            print("\n\n[%] Done. Downloaded {} images.".format(download_count))

        if prev_downloads == download_count:
            pages_without_new_downloads += 1
        else:
            pages_without_new_downloads = 0

    if download_count < limit:
        if verbose:
            print(f"Unable to find {limit} images for query \"{query}\"")

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
        out_dir_for_query = os.path.join(out_dir, query_str)
        os.makedirs(out_dir_for_query)
        scrap_bing(query=query_str, output_dir=out_dir_for_query, limit=limit)

if __name__ == '__main__':
    main()
