import os

import sidusai as sai

__required_modules__ = ['pinecone']
sai.utils.validate_modules(__required_modules__)

import sidusai.plugins.pinecone.components as components
import sidusai.plugins.pinecone.skills as skills

__default_agent_name__ = 'pinecone_agent'


class PineconePlugin(sai.AgentPlugin):
    """
    Plugin that registers Pinecone components and skills for embedding, querying, and deleting records.
    """

    def __init__(self, api_key: str, index_name: str, dimension: int | None = None,
                 namespace: str | None = None, metric: str = components.__default_metric__,
                 cloud: str = components.__default_cloud__, region: str = components.__default_region__,
                 create_if_missing: bool = True, spec_kwargs: dict | None = None,
                 embedder: components.PineconeEmbedderComponent | None = None,
                 openai_api_key: str | None = None, embedding_model: str = components.__default_embedding_model__,
                 google_api_key: str | None = None, gemini_embedding_model: str = components.__default_gemini_embedding_model__):
        super().__init__()

        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        self.namespace = namespace
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.create_if_missing = create_if_missing
        self.spec_kwargs = spec_kwargs
        self.embedder = embedder
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.google_api_key = google_api_key
        self.gemini_embedding_model = gemini_embedding_model

    def apply_plugin(self, agent: sai.Agent):
        agent.add_component_builder(self._build_pinecone_index)

        if self.embedder is not None:
            agent.add_component_builder(self._build_custom_embedder)
        else:
            has_openai = self.openai_api_key is not None or os.environ.get('OPENAI_API_KEY') is not None
            has_gemini = self.google_api_key is not None or os.environ.get('GEMINI_API_KEY') is not None

            # Prefer Gemini if provided, otherwise OpenAI.
            if has_gemini:
                agent.add_component_builder(self._build_gemini_embedder)
            elif has_openai:
                agent.add_component_builder(self._build_openai_embedder)

        agent.add_skill(skills.pinecone_upsert_skill)
        agent.add_skill(skills.pinecone_query_skill)
        agent.add_skill(skills.pinecone_delete_skill)

    def _build_pinecone_index(self) -> components.PineconeIndexComponent:
        return components.PineconeIndexComponent(
            api_key=self.api_key,
            index_name=self.index_name,
            dimension=self.dimension,
            namespace=self.namespace,
            metric=self.metric,
            cloud=self.cloud,
            region=self.region,
            create_if_missing=self.create_if_missing,
            spec_kwargs=self.spec_kwargs
        )

    def _build_custom_embedder(self) -> components.PineconeEmbedderComponent:
        return self.embedder

    def _build_openai_embedder(self) -> components.OpenAiEmbeddingComponent:
        return components.OpenAiEmbeddingComponent(
            api_key=self.openai_api_key,
            model=self.embedding_model
        )

    def _build_gemini_embedder(self) -> components.GeminiEmbeddingComponent:
        return components.GeminiEmbeddingComponent(
            api_key=self.google_api_key,
            model=self.gemini_embedding_model
        )


class PineconeAgent(sai.Agent):
    """
    Convenience agent that only registers Pinecone skills. Use for non-chat batch operations.
    """

    def __init__(self, api_key: str, index_name: str, dimension: int | None = None,
                 namespace: str | None = None, plugins: list[sai.AgentPlugin] | None = None):
        super().__init__(__default_agent_name__)

        plugins = plugins if plugins is not None else []
        pinecone_plugin = PineconePlugin(
            api_key=api_key,
            index_name=index_name,
            dimension=dimension,
            namespace=namespace
        )
        plugins.append(pinecone_plugin)

        for plugin in plugins:
            plugin.apply_plugin(self)
