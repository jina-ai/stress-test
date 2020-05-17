"""
Get text file from URL and save it to disk for posterior usage.

The used text file is the book "El Quijote" in Spanish.
It is obtained from Project Gutenberg where many free cultural books can
be downloaded.
"""

import os
import urllib.request


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

QUIJOTE_URL = "https://www.gutenberg.org/cache/epub/2000/pg2000.txt"
QUIJOTE_TXT = "ElQuijote.txt"


def download(url : str, output_file : str):
    """
    Download a text file from the given URL and save it to output_file.
    """

    response = urllib.request.urlopen(url)
    data = response.read().decode()
    with open(output_file, "w") as f:
        f.write(data)


def get_data(url : str, output_dir : str, output_file : str):
    """
    Download data if it is not in output_file, and read output_file bytes.
    """

    output_file = os.path.join(output_dir, output_file)
    if not os.path.exists(output_file):
        os.makedirs(output_dir, exist_ok=True)
        download(url, output_file)
    data = None
    with open(output_file, "rb") as f:
        data = f.read()
    return data


def get_bytes(repeat=1):
    """
    Get byte array of text from the QUIJOTE_URL.

    :param repeat: Number of times to repeat the byte array to generate
        extremely large data.
    """
    assert repeat > 0
    data = get_data(QUIJOTE_URL, DATA_DIR, QUIJOTE_TXT)
    raw_bytes = b"".join(data for _ in range(repeat))
    return raw_bytes

