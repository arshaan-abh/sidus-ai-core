import sidusai as sai

import sidusai.plugins.pinecone.components as components


class PineconeUpsertValue(sai.AgentValue):
    """
    Represents a batch of items to upsert.
    Each item must contain id and either 'text' or 'vector'/'values'.
    """

    def __init__(self, items: list[dict], namespace: str | None = None):
        super().__init__()
        self.items = items
        self.namespace = namespace


class PineconeUpsertResult(sai.AgentValue):
    def __init__(self, upserted_count: int, namespace: str | None = None):
        super().__init__()
        self.upserted_count = upserted_count
        self.namespace = namespace


class PineconeQueryValue(sai.AgentValue):
    """
    Query request. Provide either text (will be embedded) or a raw vector.
    """

    def __init__(self, text: str = None, vector: list[float] | None = None, top_k: int = 5,
                 namespace: str | None = None, filter: dict | None = None, include_metadata: bool = True):
        super().__init__()
        self.text = text
        self.vector = vector
        self.top_k = top_k
        self.namespace = namespace
        self.filter = filter
        self.include_metadata = include_metadata


class PineconeQueryResult(sai.AgentValue):
    def __init__(self, matches: list, namespace: str | None, query_text: str | None, query_vector: list[float],
                 top_k: int):
        super().__init__()
        self.matches = matches
        self.namespace = namespace
        self.query_text = query_text
        self.query_vector = query_vector
        self.top_k = top_k

    def to_context_messages(self, role: str = 'system', key: str = 'context'):
        """
        Build lightweight context messages for chat-based agents.
        """
        if self.matches is None:
            return []
        parts = []
        for m in self.matches:
            _id = m['id'] if 'id' in m else None
            score = m['score'] if 'score' in m else None
            metadata = m['metadata'] if 'metadata' in m else {}
            text = metadata['text'] if isinstance(metadata, dict) and 'text' in metadata else ''
            parts.append(f'[{_id}] score={score} {text}')
        content = '\n'.join(parts)
        return [{'role': role, 'content': f'{key}:\n{content}'}] if content else []


class PineconeDeleteValue(sai.AgentValue):
    def __init__(self, ids: list[str] | None = None, namespace: str | None = None,
                 filter: dict | None = None, delete_all: bool = False):
        super().__init__()
        self.ids = ids
        self.namespace = namespace
        self.filter = filter
        self.delete_all = delete_all


class PineconeDeleteResult(sai.AgentValue):
    def __init__(self, deleted_count: int, namespace: str | None = None):
        super().__init__()
        self.deleted_count = deleted_count
        self.namespace = namespace


def pinecone_upsert_skill(value: PineconeUpsertValue, index: components.PineconeIndexComponent,
                          embedder: components.PineconeEmbedderComponent = None) -> PineconeUpsertResult:
    return index.upsert(value, embedder)


def pinecone_query_skill(value: PineconeQueryValue, index: components.PineconeIndexComponent,
                         embedder: components.PineconeEmbedderComponent = None) -> PineconeQueryResult:
    return index.query(value, embedder)


def pinecone_delete_skill(value: PineconeDeleteValue, index: components.PineconeIndexComponent) -> PineconeDeleteResult:
    return index.delete(value)
