from dataclasses import dataclass
from typing import Literal
import os, requests

from ..utils.urls import *


@dataclass
class Photo:
    """
    Represents a product photo.

    Args:
        file_name (str): The file name corresponding to the image (e.g. "cea11c6ef934dff6c6a018df3b757b8d.jpg")
    """

    file_name: str

    def __post_init__(self):
        if is_url(self.file_name):
            self.file_name = get_file_path(self.file_name)

        self.url = f"https://prod-mercadona.imgix.net/images/{self.file_name}"

    def get_size(
        self, width: int, height: int, fit_mode: Literal["crop", "fit"] = "crop"
    ) -> str:
        """
        Generates a resized image URL based on specified width, height, and fit mode.

        Args:
            width (int): Desired width of the image.
            height (int): Desired height of the image.
            fit_mode (str, optional): Fit mode for resizing, default is 'crop'.

        Returns:
            str: Resized image URL.
        """
        return f"{self.url}?fit={fit_mode}&h={height}&w={width}"

    def save(self, path: str, width: int = None, height: int = None, fit_mode="crop"):
        """
        Downloads and saves the photo to a specified path.

        Args:
            path (str): Path where the photo will be saved.
            width (int, optional): Desired width of the downloaded photo.
            height (int, optional): Desired height of the downloaded photo.
            fit_mode (str, optional): Fit mode for resizing, default is 'crop'.
        """
        photo_url = (
            self.get_size(width, height, fit_mode) if width and height else self.url
        )
        try:
            response = requests.get(photo_url)
            response.raise_for_status()

            # Ensure the directory exists
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(path, "wb") as file:
                file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the photo: {e}")
