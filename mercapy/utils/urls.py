from urllib.parse import urlparse
import os


def is_url(string):
    parsed_url = urlparse(string)
    return parsed_url.scheme in ("http", "https", "ftp")


def get_file_path(url):
    return os.path.basename(urlparse(url).path)
