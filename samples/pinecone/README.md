# Pinecone plugin sample

This sample shows how to use the Pinecone plugin to embed text with OpenAI, upsert records, run similarity queries, and delete data from a Pinecone index.

## Prerequisites

1. Install dependencies from the repo root:
   ```bash
   pip install -e . -r requirements.txt
   ```
   `pip install -e .` makes the `sidusai` package importable when running the sample from this repo.
2. Set environment variables:
   ```bash
   export PINECONE_API_KEY="<your-pinecone-api-key>"
   # Choose one embedder:
   export OPENAI_API_KEY="<your-openai-api-key>"
   # OR
   export GEMINI_API_KEY="<your-gemini-api-key>"
   # Optional overrides
   export PINECONE_INDEX_NAME="sidusai-pinecone-sample"
   export PINECONE_NAMESPACE="demo"
   # If not set: defaults to 1536 for OpenAI, 768 for Gemini
   export PINECONE_DIMENSION="1536"
   ```
   Default embedder is OpenAI `text-embedding-3-small` (1536 dims). If `GEMINI_API_KEY` is set, the sample uses Gemini `text-embedding-004` (768 dims). Override `PINECONE_DIMENSION` if you use a different model.

## What it does

- Creates/uses a Pinecone index (serverless) with the provided name.
- Uses the default OpenAI embedder to turn sample documents into embeddings.
- Upserts three records with metadata containing their text.
- Runs a similarity query for `"historic landmarks in Asia"` and prints the top matches with scores and stored text.
- Deletes the inserted records from the namespace.
 - Prints index stats after upsert and delete to verify counts.

## Run the sample

```bash
python samples/pinecone/main.py
# or without editable install:
# PYTHONPATH=. python samples/pinecone/main.py
```

Expected output outline:

- Upsert confirmation with count
- Query results listing ids, scores, and text snippets
- Delete confirmation with count (delete count may be 0; index stats confirm removal)
