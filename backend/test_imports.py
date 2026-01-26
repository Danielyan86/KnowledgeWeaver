#!/usr/bin/env python3
"""Test all imports after refactoring"""

print("Testing imports after backend refactoring...\n")

# Test core imports
print("1. Testing core package imports...")
from backend.core.storage import get_neo4j_storage, get_vector_store
from backend.core.embeddings import get_embedding_service
print("   ✓ Core imports successful")

# Test extraction imports
print("2. Testing extraction package imports...")
from backend.extraction import (
    KnowledgeGraphExtractor,
    AsyncKnowledgeGraphExtractor,
    KnowledgeGraphNormalizer,
    EntityFilter
)
print("   ✓ Extraction imports successful")

# Test retrieval imports
print("3. Testing retrieval package imports...")
from backend.retrieval import get_retriever, get_qa_engine
from backend.retrieval.prompts import QueryType
print("   ✓ Retrieval imports successful")

# Test management imports
print("4. Testing management package imports...")
from backend.management import get_kg_manager, get_progress_tracker
print("   ✓ Management imports successful")

# Test backward compatibility through backend/__init__.py
print("5. Testing backward compatibility imports...")
from backend import (
    get_neo4j_storage,
    get_vector_store,
    get_embedding_service,
    KnowledgeGraphExtractor,
    get_kg_manager,
    get_qa_engine
)
print("   ✓ Backward compatibility imports successful")

print("\n✓ All imports successful!")
print("Backend refactoring completed successfully.")
