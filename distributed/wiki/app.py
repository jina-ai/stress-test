from jina import Flow, Document, DocumentArray

f = Flow.load_config('local/index.yml')
d1 = Document(text = 'foo1 is foo fool full fu')
d2 = Document(text = 'foo2 is foo fool full fu')
d3 = Document(text = 'foo3 is foo fool full fu')


with f:
    f.index(inputs=DocumentArray([d1, d2, d3]), on_done=print)
