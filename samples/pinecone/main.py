import os
import sidusai as sai
import sidusai.plugins.pinecone as pc
import sidusai.plugins.pinecone.skills as pc_skills
import sidusai.plugins.pinecone.components as pc_components
import time
import traceback

INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME', 'sidusai-pinecone-sample')
NAMESPACE = os.environ.get('PINECONE_NAMESPACE', 'demo')

_dimension_env = os.environ.get('PINECONE_DIMENSION')
gemini_api_key = os.environ.get('GEMINI_API_KEY')
openai_api_key = os.environ.get('OPENAI_API_KEY')
if _dimension_env is not None:
    DIMENSION = int(_dimension_env)
else:
    # Default dimension aligns with embedder choice
    DIMENSION = 768 if gemini_api_key is not None else 1536

pinecone_api_key = os.environ.get('PINECONE_API_KEY')


class PineconeSampleAgent(sai.Agent):
    def __init__(self):
        super().__init__('pinecone_sample_agent')

        pinecone_plugin = pc.PineconePlugin(
            api_key=pinecone_api_key,
            index_name=INDEX_NAME,
            dimension=DIMENSION,
            namespace=NAMESPACE,
            google_api_key=gemini_api_key,
        )
        pinecone_plugin.apply_plugin(self)

        # Log any unhandled exception from task execution
        self.add_exception_handler_method(self._log_exception, [Exception])
        # Skills are called synchronously below for a deterministic sample flow.

    def upsert(self, items: list[dict]):
        print(f'[upsert] namespace={NAMESPACE} items={[i["id"] for i in items]}')
        value = pc_skills.PineconeUpsertValue(items, namespace=NAMESPACE)
        index = self.ctx.components[pc_components.PineconeIndexComponent]
        embedder = self.ctx.components[pc_components.PineconeEmbedderComponent]
        res = index.upsert(value, embedder)
        self._print_upsert(res)
        return res

    def query(self, text: str, top_k: int = 3):
        print(f'[query] namespace={NAMESPACE} text="{text}" top_k={top_k}')
        value = pc_skills.PineconeQueryValue(text=text, top_k=top_k, namespace=NAMESPACE, include_metadata=True)
        index = self.ctx.components[pc_components.PineconeIndexComponent]
        embedder = self.ctx.components[pc_components.PineconeEmbedderComponent]
        res = index.query(value, embedder)
        self._print_query(res)
        return res

    def delete(self, ids: list[str]):
        print(f'[delete] namespace={NAMESPACE} ids={ids}')
        value = pc_skills.PineconeDeleteValue(ids=ids, namespace=NAMESPACE)
        index = self.ctx.components[pc_components.PineconeIndexComponent]
        res = index.delete(value)
        self._print_delete(res)
        return res

    @staticmethod
    def _print_upsert(value: pc_skills.PineconeUpsertResult):
        print(f'[upsert:done] upserted_count={value.upserted_count} namespace={value.namespace}')

    @staticmethod
    def _print_query(value: pc_skills.PineconeQueryResult):
        matches = value.matches if value.matches is not None else []
        print(f'[query:done] top_k={value.top_k} namespace={value.namespace} matches={len(matches)}')
        if len(matches) == 0:
            print('[query:done] no matches returned')
            return

        print('\nTop matches:')
        for match in matches:
            _id = match["id"]
            score = match["score"]
            metadata = match["metadata"] if "metadata" in match else {}
            text = metadata["text"] if isinstance(metadata, dict) and "text" in metadata else ''
            print(f'- id={_id} score={score:.4f} text="{text}"')

    @staticmethod
    def _print_delete(value: pc_skills.PineconeDeleteResult):
        print(f'[delete:done] deleted_count={value.deleted_count} namespace={value.namespace}')

    def print_index_stats(self, label: str = None):
        index = self.ctx.components[pc_components.PineconeIndexComponent]
        stats = index.index.describe_index_stats() if hasattr(index.index, 'describe_index_stats') else {}
        prefix = f'[stats:{label}]' if label is not None else '[stats]'
        print(f'{prefix} {stats}')
        return stats

    @staticmethod
    def _log_exception(exception: Exception):
        print(f'[error] {type(exception).__name__}: {exception}')
        traceback.print_exception(exception)


def build_sample_records():
    return [
        {
            'id': 'doc-1',
            'text': 'The Eiffel Tower is a wrought-iron lattice tower in Paris built in 1889.',
            'metadata': {'text': 'The Eiffel Tower is a wrought-iron lattice tower in Paris built in 1889.'}
        },
        {
            'id': 'doc-2',
            'text': 'The Great Wall of China is a series of fortifications made of stone and earthen works.',
            'metadata': {'text': 'The Great Wall of China is a series of fortifications made of stone and earthen works.'}
        },
        {
            'id': 'doc-3',
            'text': 'Mount Fuji is the highest mountain in Japan and an active stratovolcano.',
            'metadata': {'text': 'Mount Fuji is the highest mountain in Japan and an active stratovolcano.'}
        },
    ]


def main():
    if pinecone_api_key is None:
        raise ValueError('PINECONE_API_KEY environment variable is not set')
    if openai_api_key is None and gemini_api_key is None:
        raise ValueError('OPENAI_API_KEY or GEMINI_API_KEY must be set to build embeddings')

    agent = PineconeSampleAgent()
    agent.application_build()

    embedder = agent.ctx.components[pc_components.PineconeEmbedderComponent]
    embedder_name = type(embedder).__name__ if embedder is not None else 'unknown'

    print(f'Using index="{INDEX_NAME}" namespace="{NAMESPACE}" dimension={DIMENSION} embedder={embedder_name}')

    records = build_sample_records()

    print('Upserting records...')
    agent.upsert(records)
    time.sleep(1)
    stats_after_upsert = agent.print_index_stats(label='after-upsert')
    namespace_stats = stats_after_upsert.get('namespaces', {}).get(NAMESPACE, {})
    count_after_upsert = namespace_stats.get('vector_count', 0)
    if count_after_upsert == 0:
        raise RuntimeError('Upsert completed but no vectors found in namespace. Please check credentials and index settings.')

    print('\nQuerying for "historic landmarks in Asia"...')
    agent.query('historic landmarks in Asia', top_k=3)

    print('\nDeleting inserted records...')
    agent.delete([r['id'] for r in records])
    time.sleep(1)
    stats_after_delete = agent.print_index_stats(label='after-delete')
    namespace_stats_after_delete = stats_after_delete.get('namespaces', {}).get(NAMESPACE, {})
    count_after_delete = namespace_stats_after_delete.get('vector_count', 0)
    if count_after_delete > 0:
        print(f'[warn] Namespace still has {count_after_delete} vectors after delete.')


if __name__ == '__main__':
    main()
