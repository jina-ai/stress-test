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
        Segments text into sequences of two words

        :param text: the text data
        :returns: A list of documents with the extracted data
        :rtype: List[Dict]
        """
        chunks = []
        joined_words = []
        for word in text.split(" "):
            joined_words.append(word)
            if len(joined_words) == 2:
                self._append_word(chunks, joined_words)
                joined_words = []
        if len(joined_words) > 0:
            self._append_word(chunks, joined_words)

        return chunks

    def _append_word(self, chunks, joined_words):
        chunks.append(dict(text=' '.join([word for word in joined_words]), weight=1.0, mime_type='text/plain'))

