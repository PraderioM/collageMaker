from glob import glob
import os
import urllib
import re

from bing_image_downloader import downloader
from progressbar import progressbar, ProgressBar

from input_request_tools import get_out_path, get_string, get_integer

# The bing app is overwritten so that the process halts after a specified number of pages unable to download new images.
def run(self, no_new_downloads_limit: int = 10, verbose: bool= True):
    pages_without_new_downloads = 0
    bar = ProgressBar(self.limit)
    while (self.download_count < self.limit) and (pages_without_new_downloads < no_new_downloads_limit):
        if verbose:
            print('\n\n[!!]Indexing page: {}\n'.format(self.page_counter + 1))
        # Parse the page source and download pics
        request_url = 'https://www.bing.com/images/async?q=' + urllib.parse.quote_plus(self.query) \
                      + '&first=' + str(self.page_counter) + '&count=' + str(self.limit) \
                      + '&adlt=' + self.adult + '&qft=' + self.filters
        request = urllib.request.Request(request_url, None, headers=self.headers)
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf8')
        links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)

        if verbose:
            print("[%] Indexed {} Images on Page {}.".format(len(links), self.page_counter + 1))
            print("\n===============================================\n")

        prev_downloads = self.download_count
        for link in links:
            if self.download_count < self.limit:
                self.download_image(link)
                bar.update(self.download_count)
            else:
                if verbose:
                    print("\n\n[%] Done. Downloaded {} images.".format(self.download_count))
                    print("\n===============================================\n")
                break

        self.page_counter += 1
        if prev_downloads == self.download_count:
            pages_without_new_downloads += 1
        else:
            pages_without_new_downloads = 0

    if self.download_count < self.limit:
        if verbose:
            print(f"Unable to find {self.limit} images for query \"{self.query}\"")

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
        downloader.run = run
        downloader.download(query_str,
                            limit=limit,
                            output_dir=out_dir,
                            adult_filter_off=True,
                            force_replace=False,
                            timeout=60,
                            verbose=False)


if __name__ == '__main__':
    main()
