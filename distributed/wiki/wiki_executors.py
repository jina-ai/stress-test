import os
import json
import errno
import torch
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex
from typing import Dict, Optional, List

from transformers import AutoModel, AutoTokenizer
from jina import Executor, DocumentArray, requests, Document
from jina.types.arrays.memmap import DocumentArrayMemmap


class Segmenter(Executor):
    @requests
    def segment(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            joined_tokens = []
            chunks = DocumentArray()
            for token in doc.text.split(' '):
                joined_tokens.append(token)
                if len(joined_tokens) == 2:
                    chunks.append(
                        Document(
                            weight=1.0,
                            mime_type='text/plain',
                            text=' '.join([word for word in joined_tokens]),
                        )
                    )
                    joined_tokens = []
            if len(joined_tokens) > 0:
                chunks.append(
                    Document(
                        weight=1.0,
                        mime_type='text/plain',
                        text=' '.join([word for word in joined_tokens]),
                    )
                )

            doc.chunks = chunks


class TextEncoder(Executor):
    """Transformer executor class"""

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'sentence-transformers/paraphrase-mpnet-base-v2',
        base_tokenizer_model: Optional[str] = None,
        pooling_strategy: str = 'mean',
        layer_index: int = -1,
        max_length: Optional[int] = None,
        acceleration: Optional[str] = None,
        embedding_fn_name: str = '__call__',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.base_tokenizer_model = (
            base_tokenizer_model or pretrained_model_name_or_path
        )
        self.pooling_strategy = pooling_strategy
        self.layer_index = layer_index
        self.max_length = max_length
        self.acceleration = acceleration
        self.embedding_fn_name = embedding_fn_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_tokenizer_model)
        self.model = AutoModel.from_pretrained(
            self.pretrained_model_name_or_path, output_hidden_states=True
        )
        self.model.to(torch.device('cpu'))

    def _compute_embedding(self, hidden_states: 'torch.Tensor', input_tokens: Dict):
        fill_vals = {'cls': 0.0, 'mean': 0.0, 'max': -np.inf, 'min': np.inf}
        fill_val = torch.tensor(
            fill_vals[self.pooling_strategy], device=torch.device('cpu')
        )

        layer = hidden_states[self.layer_index]
        attn_mask = input_tokens['attention_mask'].unsqueeze(-1).expand_as(layer)
        layer = torch.where(attn_mask.bool(), layer, fill_val)

        embeddings = layer.sum(dim=1) / attn_mask.sum(dim=1)
        return embeddings.cpu().numpy()

    @requests
    def encode(self, docs: 'DocumentArray', *args, **kwargs):

        chunks = DocumentArray(
            list(
                filter(lambda d: d.mime_type == 'text/plain', docs.traverse_flat(['c']))
            )
        )

        texts = chunks.get_attributes('text')

        with torch.no_grad():

            if not self.tokenizer.pad_token:
                self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                self.model.resize_token_embeddings(len(self.tokenizer.vocab))

            input_tokens = self.tokenizer(
                texts,
                max_length=self.max_length,
                padding='longest',
                truncation=True,
                return_tensors='pt',
            )
            input_tokens = {
                k: v.to(torch.device('cpu')) for k, v in input_tokens.items()
            }

            outputs = getattr(self.model, self.embedding_fn_name)(**input_tokens)
            if isinstance(outputs, torch.Tensor):
                return outputs.cpu().numpy()
            hidden_states = outputs.hidden_states

            embeds = self._compute_embedding(hidden_states, input_tokens)
            for doc, embed in zip(chunks, embeds):
                doc.embedding = embed

        return chunks


class AnnoyIndexer(Executor):

    ANNOY_INDEX_FILE_NAME = 'annoy.ann'
    ANNOY_INDEX_MAPPING_NAME = (
        'map.json'  # this map stores int id and docid, annoy only allows add int as id.
    )

    def __init__(
        self,
        top_k: int = 10,
        num_dim: int = 768,
        num_trees: int = 10,
        metric: str = 'angular',
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.top_k = top_k
        self.metric = metric
        self.num_dim = num_dim
        self.num_trees = num_trees
        self.id_docid_map = {}
        self.id_docid_map_flag = 0
        self.request_type = None
        self.index_base_dir = f'{os.environ["JINA_WORKDIR"]}/annoy/'
        self.index_path = self.index_base_dir + self.ANNOY_INDEX_FILE_NAME
        self.index_map_path = self.index_base_dir + self.ANNOY_INDEX_MAPPING_NAME
        self.index = AnnoyIndex(self.num_dim, 'angular')
        if os.path.exists(self.index_path) and os.path.exists(self.index_map_path):
            self._load_index()

    def _load_index(self):
        self.index.load(self.index_path)
        with open(self.index_map_path, 'r') as f:
            self.id_docid_map = json.load(f)

    @requests(on='/delete')
    def delete(self, **kwargs):
        try:
            os.remove(self.index_path)
            os.remove(self.index_map_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self.request_type = '/index'
        if os.path.exists(self.index_path) or os.path.exists(self.index_map_path):
            raise FileExistsError(
                'Index already exist, please remove workspace and index again.'
            )
        for doc in docs:
            self.id_docid_map[self.id_docid_map_flag] = doc.id
            self.index.add_item(self.id_docid_map_flag, doc.embedding)
            self.id_docid_map_flag += 1

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            indices, dists = self.index.get_nns_by_vector(
                doc.embedding, self.top_k, include_distances=True
            )
            for idx, dist in zip(indices, dists):
                match = Document(id=self.id_docid_map[str(idx)])
                match.score.value = 1 / (1 + dist)
                doc.matches.append(match)  # chunk level matches

    def close(self):
        if self.request_type == '/index':
            self.index.build(self.num_trees)
            Path(self.index_base_dir).mkdir(parents=True, exist_ok=True)
            self.index.save(self.index_path)
            with open(self.index_map_path, 'w') as f:
                json.dump(self.id_docid_map, f)


class KeyValueIndexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArrayMemmap(self.workspace + '/kv-idx')

    @property
    def save_path(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        return os.path.join(self.workspace, 'kv.json')

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def query(self, docs: DocumentArray, **kwargs):
        indexed_docs = DocumentArray(self._docs)
        parent_child_map = {}
        for doc in indexed_docs:
            parent_child_map[doc.id] = [item.id for item in doc.chunks]
        for doc in docs:  # chunks of matches
            for match in doc.matches:  # chunk level matches
                for k, v in parent_child_map.items():
                    if match.id in v:
                        extracted_doc = self._docs[k]
                        match.update(extracted_doc)


class AggregateRanker(Executor):
    @requests(on='/search')
    def rank(self, docs: DocumentArray, **kwargs) -> 'DocumentArray':
        """
        :param docs: the doc which gets bubbled up matches
        :param kwargs: not used (kept to maintain interface)
        """
        # TODO NEED TO TAKE AVERAGE ON CHUNKS
        docs.sort(key=lambda item: item.score.value, reverse=True)
