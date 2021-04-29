from typing import Dict, List

from jina.executors.decorators import single
from jina.executors.segmenters import BaseSegmenter


class TextSegmenter(BaseSegmenter):
    """
    :class:`TextSegmenter` simply store text into chunks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single(slice_nargs=1)
    def segment(self, text: str, *args, **kwargs) -> List[Dict]:
        """
        Segments text into words

        :param text: the text data
        :returns: A list of documents with the extracted data
        :rtype: List[Dict]
        """
        chunks = []
        for word in text.split(" "):
            chunks.append(dict(text=word, weight=1.0, mime_type='text/plain'))
        return chunks

