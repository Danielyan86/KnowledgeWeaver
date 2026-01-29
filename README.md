# KnowledgeWeaver

Knowledge Graph + RAG Hybrid Question Answering System

[中文文档](README_CN.md) | English

## Overview

KnowledgeWeaver is an intelligent question-answering system that combines Knowledge Graph (KG) and Retrieval-Augmented Generation (RAG) technologies. The system automatically extracts entities and relationships from documents, builds a knowledge graph, and provides accurate, context-aware answers through a combination of vector retrieval and graph reasoning.

## Core Features

- **Document Processing**: Automatic parsing and chunking of PDF and TXT format documents
- **Knowledge Extraction**: LLM-based entity and relationship extraction
- **Knowledge Graph**: Automatic construction, normalization, and storage of knowledge graphs
- **Hybrid Retrieval**: Combines vector similarity retrieval and graph structure retrieval
- **Intelligent Q&A**: Context-aware question answering based on retrieval results
- **Visualization**: Interactive knowledge graph visualization based on D3.js

## System Architecture

### Application Architecture

![Architecture Diagram](docs/architecture/architecture-en.png)

### AWS Deployment Architecture

For AWS deployment architecture and infrastructure design, see:
- [Interactive AWS Architecture Diagram](docs/architecture/aws-architecture-diagram-en.html)
- [AWS Deployment Guide](docs/deployment/AWS_DEPLOYMENT_GUIDE.md)

### Processing Pipeline

1. **Input Layer**: Receives documents (txt/pdf)
2. **Processing Layer**:
   - Document chunking
   - LLM entity and relationship extraction
   - Knowledge merging and normalization
3. **Storage Layer**:
   - Neo4j graph database (knowledge graph storage)
   - ChromaDB vector database (semantic search)
4. **Service Layer**:
   - FastAPI backend service
   - Hybrid retriever (KG + RAG)
   - QA engine
5. **Frontend Layer**:
   - D3.js knowledge graph visualization
   - Chat Q&A interface

## Tech Stack

### Backend
- **FastAPI**: High-performance web framework
- **LLM Integration**: OpenAI API / Custom endpoints
- **Neo4j**: Graph database for knowledge graph storage
- **ChromaDB**: Vector database for semantic search
- **Jinja2**: Prompt template engine

### Frontend
- **D3.js**: Knowledge graph visualization
- **JavaScript**: Interactive logic

### External Services
- **LLM API**: space.ai-builders.com

### Observability (Optional)
- **Phoenix**: AI observability and evaluation platform (OpenTelemetry-based)
  - [Integration Guide](docs/PHOENIX_INTEGRATION.md)
  - [Comparison with Langfuse](docs/OBSERVABILITY_COMPARISON.md)
- **Langfuse**: LLM observability and monitoring
  - [Setup Guide](docs/LANGFUSE_GUIDE.md)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file and configure:

```bash
# LLM Configuration
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here

# Extraction LLM (Gemini API - Free)
EXTRACTION_LLM_BACKEND=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j Configuration
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 3. Start Service

**Option 1: Quick Start (Recommended for Development)**
```bash
./scripts/start_dev.sh
```

**Option 2: Full Start with Checks (Recommended for First Run)**
```bash
./scripts/start.sh
```

**Option 3: Manual Start**
```bash
python -m backend.server
```

**Other Commands:**
```bash
# Check service status
./scripts/status.sh

# Stop service
./scripts/stop.sh

# Restart service
./scripts/restart.sh
```

See [scripts/README.md](scripts/README.md) for detailed documentation.

### 4. Access the Service

- **Frontend UI**: http://localhost:9621
- **API Docs**: http://localhost:9621/docs
- **Health Check**: http://localhost:9621/health

### Process Documents

```bash
python backend/process_book.py
```

## User Guide

### Starting Local Services

#### 1. Start Neo4j Database

**Option A: Docker (Recommended)**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $(pwd)/data/neo4j/data:/data \
  neo4j:latest
```

Access Neo4j Browser at: http://localhost:7474

**Option B: Native Installation**

Download and install from: https://neo4j.com/download/

#### 2. Start FastAPI Backend

```bash
python -m backend.server
```

The API will start at: http://localhost:9621

- API Documentation: http://localhost:9621/docs
- Health Check: http://localhost:9621/health

#### 3. (Optional) Start Observability Tools

**Option A: Langfuse - For Production Monitoring**

Langfuse provides detailed LLM call tracking, cost analysis, and production monitoring.

```bash
# 1. Configure environment variables in .env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com  # or your self-hosted URL

# 2. Install Langfuse
pip install langfuse>=2.0.0

# 3. Restart backend service
python -m backend.server
```

Visit https://cloud.langfuse.com to view traces.

For self-hosted deployment, see: [Langfuse Complete Guide](docs/observability/LANGFUSE_GUIDE.md)

**Option B: Phoenix - For Development and Evaluation**

Phoenix offers zero-code tracing, experiment tracking, and prompt optimization.

```bash
# 1. Start Phoenix server (Docker)
docker run -d \
  --name phoenix \
  -p 6006:6006 \
  -p 4317:4317 \
  -v $(pwd)/data/phoenix:/data \
  arizephoenix/phoenix:latest

# 2. Configure environment variables in .env
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# 3. Install Phoenix packages
pip install arize-phoenix arize-phoenix-otel openinference-instrumentation-openai

# 4. Restart backend service
python -m backend.server
```

Access Phoenix UI at: http://localhost:6006

For detailed setup and comparison, see: [Phoenix Integration Guide](docs/observability/PHOENIX_INTEGRATION.md)

### Using the System

#### Upload and Process Documents

**Via API (Asynchronous - Recommended)**

```bash
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@your_document.txt"

# Response: {"doc_id": "abc123", "status": "processing"}

# Check progress
curl "http://localhost:9621/documents/progress/abc123"
```

**Via API (Synchronous)**

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@your_document.pdf"
```

**Via Command Line**

```bash
python backend/extraction/async_extractor.py path/to/document.txt
```

#### Query the Knowledge Graph

**Ask Questions**

```bash
curl -X POST "http://localhost:9621/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is knowledge graph?",
    "mode": "auto",
    "n_hops": 2,
    "top_k": 5
  }'
```

Query modes:
- `auto`: Automatically choose best strategy
- `kg_only`: Knowledge graph only
- `rag_only`: Vector retrieval only
- `hybrid`: Combine both KG and RAG
- `kg_first`: Try KG first, fallback to RAG
- `rag_first`: Try RAG first, fallback to KG

**Semantic Search**

```bash
curl -X POST "http://localhost:9621/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "investment strategies",
    "search_type": "all",
    "top_k": 10
  }'
```

Search types:
- `all`: Search both chunks and entities
- `chunks`: Search document chunks only
- `entities`: Search entities only

#### Visualize Knowledge Graph

**Get Full Graph**

```bash
curl "http://localhost:9621/graphs"
```

**Get Document-Specific Graph**

```bash
curl "http://localhost:9621/documents/abc123"
```

**View in Browser**

Open `frontend/index.html` in your browser to interact with the D3.js visualization.

#### Monitor and Manage

**View Statistics**

```bash
# Knowledge graph stats
curl "http://localhost:9621/stats"

# Vector store stats
curl "http://localhost:9621/vector-stats"
```

**List Documents**

```bash
curl "http://localhost:9621/documents"
```

**Delete Document**

```bash
curl -X DELETE "http://localhost:9621/documents/abc123"
```

### Configuration Reference

Edit `.env` file to customize settings:

```bash
# === LLM Configuration ===
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key
LLM_MODEL=deepseek  # or other model

# === Neo4j Configuration ===
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_MAX_POOL_SIZE=50
NEO4J_BATCH_SIZE=500

# === Processing Configuration ===
CONCURRENT_REQUESTS=5  # Concurrent LLM requests
MAX_RETRIES=3
CHUNK_SIZE=800
CHUNK_OVERLAP_RATIO=0.5

# === Observability (Optional) ===
# Langfuse
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Phoenix
PHOENIX_ENABLED=false
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# === Service Configuration ===
HOST=0.0.0.0
PORT=9621
```

### Troubleshooting

**Neo4j Connection Failed**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs neo4j

# Verify credentials in .env match your Neo4j setup
```

**API Server Not Starting**
```bash
# Check port availability
lsof -i :9621

# Check logs for detailed error messages
python -m backend.server
```

**Document Processing Stuck**
```bash
# Check progress
curl "http://localhost:9621/documents/progress/YOUR_DOC_ID"

# Check checkpoint files
ls -la data/checkpoints/YOUR_DOC_ID/

# Restart processing (will resume from checkpoint)
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@same_document.txt"
```

**LLM API Errors**
```bash
# Verify API key is correct
# Check LLM_BINDING_HOST is accessible
# Review rate limits and quotas
```

For more detailed guides, see the [Documentation Index](docs/README.md).

## Project Structure

```
KnowledgeWeaver/
├── backend/              # Backend code
│   ├── server.py        # FastAPI service
│   ├── extractor.py     # Knowledge extraction
│   ├── hybrid_retriever.py  # Hybrid retriever
│   ├── qa_engine.py     # QA engine
│   ├── vector_store.py  # Vector storage
│   ├── embedder.py      # Text embedding
│   └── prompts/         # Prompt templates
├── frontend/            # Frontend code
│   ├── kg-config.js     # Graph configuration
│   └── kg-normalizer.js # Graph normalization
├── data/                # Data directory (gitignored)
│   ├── storage/         # Persistent storage
│   │   └── vector_db/   # Vector database (ChromaDB)
│   ├── checkpoints/     # Processing checkpoints (resume capability)
│   ├── progress/        # Progress tracking data
│   ├── inputs/          # User uploaded files
│   └── cache/           # Cache data
├── docs/                # Documentation
│   ├── architecture/    # Architecture diagrams and design documents
│   ├── deployment/      # AWS and deployment guides
│   ├── database/        # Database setup and optimization guides
│   ├── observability/   # Monitoring and observability documentation
│   ├── development/     # Development and testing guides
│   ├── security/        # Security best practices and guidelines
│   └── README.md        # Documentation index
├── logs/                # Log files (gitignored)
└── tests/               # Test cases
```

## Key Features

### Knowledge Graph Normalization
- Entity deduplication and merging
- Relationship standardization
- Information island detection and connection

### Hybrid Retrieval Strategy
- Vector similarity retrieval (RAG)
- Graph structure retrieval (KG)
- Dynamic weight fusion

### Intelligent Q&A
- Context awareness
- Multi-source information integration
- Structured answer generation

## License

MIT License
