from jina import Flow, Document, DocumentArray

f = Flow.load_config(
    './local/index.yml'
)

d1 = Document(id=1, text='foo1 is foo fool full fu')
d2 = Document(id=2, text='foo2 is foo fool full fu')
d3 = Document(id=3, text='foo3 is foo fool full fu')


def print_matches(req):  # the callback function invoked when task is done
    for idx, d in enumerate(req.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.score.value:2f}: "{d.text}"')


with f:
    f.index(inputs=DocumentArray([d1, d2, d3]))

with Flow.load_config(
    './local/query.yml'
) as f:
    f.search(inputs=d2, on_done=print_matches)
