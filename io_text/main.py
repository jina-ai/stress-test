"""
Run the Sentencizer executer on a lot of text data.
"""

import timeit

from jina.executors.crafters.nlp.split import Sentencizer

import data_loader


def main(data_repeat=100, repeat=3):
    """
    :param data_repeat: Number of times do you want to repeat the byte array.
    :param repeat: Number of times to repeat the test to get a more exact average time.
    """
    # Setup.
    raw_bytes = data_loader.get_bytes(repeat=data_repeat)
    sentencizer = Sentencizer()
    # Test execution.
    timer = timeit.Timer(lambda: sentencizer.craft(raw_bytes, 0))
    times = timer.repeat(repeat, 1)
    # Show results.
    mb = len(raw_bytes) / 2**20
    time_mean = sum(times) / repeat
    print(f"{mb:.2f}MB read {repeat} times.")
    print(f"Average per iteration: {time_mean:.6f}.")


if __name__ == "__main__":
    main()

