# Enterprise RAG Subsystem

End-to-end Retrieval-Augmented Generation (RAG) platform architecture for EAIMOS.

## Sub-modules
- `ingestion/`: Document ingestion & source synchronization.
- `parsers/`: PDF, HTML, Markdown & DOCX document parser engines.
- `cleaners/`: Text cleaning, noise reduction & normalization.
- `chunkers/`: Semantic, fixed-size & sliding-window chunking.
- `retrievers/`: Vector & full-text document retrievers.
- `rerankers/`: Cohere / Cross-Encoder relevance rerankers.
- `hybrid-search/`: Dense + Sparse hybrid search engine.
- `citations/`: Source attribution & citation formatting.
