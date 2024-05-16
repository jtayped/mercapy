from dataclasses import dataclass
from ..utils.urls import *


@dataclass
class Image:
    file_name: str

    def __post_init__(self):
        if is_url(self.file_name):
            self.file_name = get_file_path(self.file_name)

        self.url = f"https://prod-mercadona.imgix.net/images/{self.file_name}"

    def get_size(self, width: int, height: int) -> str:
        return f"{self.url}?fit=crop&h={height}&w={width}"

    def save_image(self, path: str, width: int = None, height: int = None):
        pass  # TODO
