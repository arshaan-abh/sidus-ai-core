import os
from typing import Any

from sidusai.core.plugin import AgentValue

__default_metric__ = 'cosine'
__default_cloud__ = 'aws'
__default_region__ = 'us-east-1'
__default_embedding_model__ = 'text-embedding-3-small'
__default_gemini_embedding_model__ = 'text-embedding-004'


class PineconeEmbedderComponent:
    """
    Base embedder contract used by Pinecone skills.
    Implementations must return a list of embedding vectors for a list of texts.
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError('Embedder must implement embed(texts)')


class OpenAiEmbeddingComponent(PineconeEmbedderComponent):
    """
    Simple OpenAI embedder. Uses the official OpenAI client and the Embeddings API.
    """

    def __init__(self, api_key: str | None = None, model: str = __default_embedding_model__):
        super().__init__()
        try:
            from openai import OpenAI
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                'openai package is required for OpenAiEmbeddingComponent. Please install it.'
            ) from e

        _api_key = api_key if api_key is not None else os.environ.get('OPENAI_API_KEY')
        if _api_key is None:
            raise ValueError('OpenAI API key is not set. Provide api_key or set OPENAI_API_KEY env variable.')

        self.model = model
        self.client = OpenAI(api_key=_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if texts is None or len(texts) == 0:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class GeminiEmbeddingComponent(PineconeEmbedderComponent):
    """
    Google Gemini embedder using the text-embedding-004 model.
    """

    def __init__(self, api_key: str | None = None, model: str = __default_gemini_embedding_model__):
        super().__init__()
        try:
            import google.generativeai as genai
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                'google-generativeai package is required for GeminiEmbeddingComponent. Please install it.'
            ) from e

        _api_key = api_key if api_key is not None else os.environ.get('GEMINI_API_KEY')
        if _api_key is None:
            raise ValueError('Gemini API key is not set. Provide api_key or set GEMINI_API_KEY env variable.')

        self.model = model
        self._genai = genai
        self._genai.configure(api_key=_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if texts is None or len(texts) == 0:
            return []

        vectors = []
        for text in texts:
            res = self._genai.embed_content(model=self.model, content=text)
            emb = res['embedding'] if isinstance(res, dict) and 'embedding' in res else None
            if emb is None:
                raise RuntimeError('Failed to get embedding from Gemini response.')
            vectors.append(emb)
        return vectors


class PineconeIndexComponent:
    """
    Wraps a Pinecone index connection and exposes upsert/query/delete helpers.
    """

    def __init__(self, api_key: str, index_name: str, dimension: int | None,
                 metric: str = __default_metric__, cloud: str = __default_cloud__, region: str = __default_region__,
                 namespace: str | None = None, create_if_missing: bool = True, spec_kwargs: dict | None = None):
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError('pinecone package is required. Please install it.') from e

        self.api_key = api_key
        self.index_name = index_name
        self.namespace = namespace
        self.metric = metric
        self.dimension = dimension
        self.cloud = cloud
        self.region = region
        self.spec_kwargs = spec_kwargs if spec_kwargs is not None else {}
        self._create_if_missing = create_if_missing

        self.client = Pinecone(api_key=self.api_key)
        self._spec_class = ServerlessSpec
        self._ensure_index()
        self.index = self.client.Index(self.index_name)
        self._sync_dimension()

    def upsert(self, value: AgentValue, embedder: PineconeEmbedderComponent | None = None):
        from sidusai.plugins.pinecone import skills
        if not isinstance(value, skills.PineconeUpsertValue):
            raise ValueError('Invalid value type for upsert. Use PineconeUpsertValue.')

        namespace = value.namespace if value.namespace is not None else self.namespace
        items = value.items if value.items is not None else []
        if len(items) == 0:
            return skills.PineconeUpsertResult(0, namespace)

        texts_to_embed = []
        text_targets = []

        records = []
        for item in items:
            if 'id' not in item:
                raise ValueError('Each upsert item must contain an "id" field.')

            record = {'id': item['id']}

            vector = item['vector'] if 'vector' in item else item['values'] if 'values' in item else None
            text = item['text'] if 'text' in item else None

            if vector is None and text is None:
                raise ValueError(f'Item {item["id"]} must contain "text" or "vector".')

            if vector is not None:
                self._validate_dimension(vector)
                record['values'] = vector
            else:
                texts_to_embed.append(text)
                text_targets.append(record)

            metadata = item['metadata'] if 'metadata' in item else None
            if metadata is not None:
                record['metadata'] = metadata

            records.append(record)

        if len(texts_to_embed) > 0:
            if embedder is None:
                raise ValueError('Embedder component is required to convert text to embeddings.')
            vectors = embedder.embed(texts_to_embed)
            if len(vectors) != len(text_targets):
                raise RuntimeError('Embedded vector count does not match input texts count.')
            for target, vector in zip(text_targets, vectors):
                self._validate_dimension(vector)
                target['values'] = vector

        response = self.index.upsert(vectors=records, namespace=namespace)
        upserted_count = 0
        if response is not None:
            if isinstance(response, dict) and 'upserted_count' in response:
                upserted_count = response['upserted_count']
            elif hasattr(response, 'upserted_count'):
                upserted_count = getattr(response, 'upserted_count')
        if upserted_count == 0:
            upserted_count = len(records)
        return skills.PineconeUpsertResult(upserted_count, namespace)

    def query(self, value: AgentValue, embedder: PineconeEmbedderComponent | None = None):
        from sidusai.plugins.pinecone import skills
        if not isinstance(value, skills.PineconeQueryValue):
            raise ValueError('Invalid value type for query. Use PineconeQueryValue.')

        namespace = value.namespace if value.namespace is not None else self.namespace
        query_vector = value.vector
        if query_vector is None:
            if value.text is None:
                raise ValueError('Query must contain text or vector.')
            if embedder is None:
                raise ValueError('Embedder component is required to convert text to embeddings.')
            vectors = embedder.embed([value.text])
            if len(vectors) == 0:
                raise RuntimeError('Embedder returned an empty vector list.')
            query_vector = vectors[0]

        self._validate_dimension(query_vector)

        response = self.index.query(
            vector=query_vector,
            top_k=value.top_k,
            namespace=namespace,
            include_metadata=value.include_metadata,
            filter=value.filter
        )

        matches = self._serialize_matches(response)
        return skills.PineconeQueryResult(
            matches=matches,
            namespace=namespace,
            query_text=value.text,
            query_vector=query_vector,
            top_k=value.top_k
        )

    def delete(self, value: AgentValue):
        from sidusai.plugins.pinecone import skills
        if not isinstance(value, skills.PineconeDeleteValue):
            raise ValueError('Invalid value type for delete. Use PineconeDeleteValue.')

        namespace = value.namespace if value.namespace is not None else self.namespace
        ids_empty = value.ids is None or (isinstance(value.ids, list) and len(value.ids) == 0)
        if not value.delete_all and ids_empty and value.filter is None:
            raise ValueError('Delete requires ids, filter, or delete_all=True')

        response = self.index.delete(
            ids=value.ids,
            namespace=namespace,
            filter=value.filter,
            delete_all=value.delete_all
        )

        deleted_count = 0
        if response is not None:
            if isinstance(response, dict) and 'deleted_count' in response:
                deleted_count = response['deleted_count']
            elif hasattr(response, 'deleted_count'):
                deleted_count = getattr(response, 'deleted_count')

        return skills.PineconeDeleteResult(
            deleted_count=deleted_count,
            namespace=namespace
        )

    def _serialize_matches(self, response: Any) -> list:
        raw_matches = []
        if response is None:
            return []
        if isinstance(response, dict):
            raw_matches = response['matches'] if 'matches' in response else []
        elif hasattr(response, 'matches'):
            raw_matches = getattr(response, 'matches')

        matches = []
        for m in raw_matches:
            if isinstance(m, dict):
                _id = m['id'] if 'id' in m else None
                _score = m['score'] if 'score' in m else None
                _values = m['values'] if 'values' in m else None
                _metadata = m['metadata'] if 'metadata' in m else None
            else:
                _id = getattr(m, 'id', None)
                _score = getattr(m, 'score', None)
                _values = getattr(m, 'values', None)
                _metadata = getattr(m, 'metadata', None)
            matches.append({
                'id': _id,
                'score': _score,
                'values': _values,
                'metadata': _metadata
            })
        return matches

    def _validate_dimension(self, vector):
        if vector is None:
            raise ValueError('Vector can not be None')
        if self.dimension is None:
            return
        if len(vector) != self.dimension:
            raise ValueError(f'Invalid vector dimension. Expected {self.dimension}, got {len(vector)}')

    def _ensure_index(self):
        existing_indexes = self.client.list_indexes()
        names = []
        if hasattr(existing_indexes, 'names'):
            try:
                names = existing_indexes.names()
            except Exception:
                names = []
        elif isinstance(existing_indexes, list):
            names = [idx['name'] if isinstance(idx, dict) and 'name' in idx else getattr(idx, 'name', None)
                     for idx in existing_indexes]
            names = [n for n in names if n is not None]

        if self.index_name in names:
            return

        if not self._create_if_missing:
            raise ValueError(f'Pinecone index "{self.index_name}" is not found.')

        if self.dimension is None:
            raise ValueError('Index does not exist and dimension is not provided to create one.')

        spec = self._spec_class(cloud=self.cloud, region=self.region, **self.spec_kwargs)
        self.client.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric=self.metric,
            spec=spec
        )

    def _sync_dimension(self):
        try:
            stats = self.index.describe_index_stats()
        except Exception:
            return
        if isinstance(stats, dict) and 'dimension' in stats:
            index_dim = stats['dimension']
            if self.dimension is None:
                self.dimension = index_dim
            elif index_dim is not None and self.dimension != index_dim:
                raise ValueError(f'Index "{self.index_name}" dimension mismatch: index={index_dim}, expected={self.dimension}')
