

def bytes_generator(num_docs, num_bytes):
    """
    Yields `num_bytes` bytes `num_docs` times
    """
    for _ in range(num_docs):
        yield b'a' * num_bytes


def get_list_of_num_docs(start, multiplier, count):
    """
    Returns list of number of docs to be indexed
    e.g. -
    For start=512, multiplier=4, count=4, returns [512, 2048, 8192, 32768]
    """
    return [start * (multiplier ** i) for i in range(count)]


def generate_filename(num_docs, num_bytes):
    """ Generates filename using num_docs & num_bytes """
    return f'docs_{num_docs}_bytes_{num_bytes}.parquet'
