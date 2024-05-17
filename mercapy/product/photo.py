from dataclasses import dataclass
from urllib.parse import urlparse
import requests
import os

from ..utils.urls import is_url, get_file_path


@dataclass
class Photo:
    file_name: str

    def __post_init__(self):
        if is_url(self.file_name):
            self.file_name = get_file_path(self.file_name)

        self.url = f"https://prod-mercadona.imgix.net/images/{self.file_name}"

    def get_size(self, width: int, height: int, fit_mode="crop") -> str:
        return f"{self.url}?fit={fit_mode}&h={height}&w={width}"

    def save(self, path: str, width: int = None, height: int = None, fit_mode="crop"):
        photo_url = (
            self.get_size(width, height, fit_mode) if width and height else self.url
        )
        try:
            response = requests.get(photo_url)
            response.raise_for_status()

            # Ensure the directory exists, if a directory is specified
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(path, "wb") as file:
                file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the photo: {e}")
