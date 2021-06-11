def segment(text: str, *args, **kwargs):
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
                _append_word(chunks, joined_words)
                joined_words = []
        if len(joined_words) > 0:
            _append_word(chunks, joined_words)

        return chunks

def _append_word(chunks, joined_words):
    chunks.append(dict(text=' '.join([word for word in joined_words]), weight=1.0, mime_type='text/plain'))


res = segment('today sis a sunny day')
from pprint import pprint
pprint(res)
