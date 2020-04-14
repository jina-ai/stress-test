import glob

from jina.flow import Flow

GIF_BLOB = '/Volumes/TOSHIBA-4T/dataset/thumblr-gif-data/*.gif'  # 'data/*.gif'
num_docs = 100000
replicas = 10


def f1():
    f = Flow().add(yaml_path='gif2chunk.yml', replicas=replicas)
    bytes_gen = (g.encode() for g in glob.glob(GIF_BLOB)[:num_docs])

    with f.build() as fl:
        fl.index(bytes_gen, batch_size=128)


def f2():
    f = Flow(logserver=True, logserver_config='test-server-config.yml').add(yaml_path='gif2chunk2.yml',
                                                                            replicas=replicas)

    def bytes_gen():
        idx = 0
        for g in glob.glob(GIF_BLOB)[:num_docs]:
            with open(g, 'rb') as fp:
                # print(f'im asking to read {idx}')
                yield fp.read()
                idx += 1

    # for idx, request in enumerate(bytes_gen()):
    #     print(idx)

    with f.build() as fl:
        fl.index(bytes_gen(), batch_size=8)


if __name__ == '__main__':
    f2()
