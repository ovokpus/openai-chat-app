"""
Preprocessed Knowledge Base

This module provides access to the preprocessed knowledge base data.
It serves as a compatibility layer for older code that expects the data in a specific format.
"""

from typing import Dict, Any, List
from .knowledge_base_data import KB_CHUNKS as KNOWLEDGE_BASE_CHUNKS

# Knowledge base metadata
KNOWLEDGE_BASE_METADATA = {
    "created_at": "2025-07-02T12:57:58.725755",
    "total_chunks": 1683,
    "total_documents": 9,
    "version": "1.0",
    "processed_files": [
        {
            "filename": "FINREP_IFRS_templates_Annex_I.xls",
            "subfolder": "finrep_templates",
            "chunk_count": 176,
            "doc_type": "excel"
        },
        {
            "filename": "FINREP_IFRS_templates_Annex_III.xlsx",
            "subfolder": "finrep_templates",
            "chunk_count": 161,
            "doc_type": "excel"
        },
        {
            "filename": "Basel_III_Implementation_Policy.md",
            "subfolder": "basel_iii",
            "chunk_count": 17,
            "doc_type": "code"
        },
        {
            "filename": "Basel_III_Finalising_post-crisis_reforms.pdf",
            "subfolder": "basel_iii",
            "chunk_count": 910,
            "doc_type": "pdf"
        },
        {
            "filename": "COREP_Own_funds_templates.xlsx",
            "subfolder": "corep_templates",
            "chunk_count": 135,
            "doc_type": "excel"
        },
        {
            "filename": "Jira_Regulatory_Issues_Export.csv",
            "subfolder": "other_regulatory",
            "chunk_count": 15,
            "doc_type": "csv"
        },
        {
            "filename": "SQL_Data_Lineage_Sample.sql",
            "subfolder": "other_regulatory",
            "chunk_count": 10,
            "doc_type": "code"
        },
        {
            "filename": "SIFMA_Third_Party_Regulation_Mapping_Matrix.xlsx",
            "subfolder": "other_regulatory",
            "chunk_count": 244,
            "doc_type": "excel"
        },
        {
            "filename": "Regulatory_Steering_Committee_Presentation.txt",
            "subfolder": "other_regulatory",
            "chunk_count": 15,
            "doc_type": "code"
        }
    ]
}

def get_preprocessed_knowledge_base() -> Dict[str, Any]:
    """Returns the preprocessed knowledge base data in the legacy format."""
    return {
        "chunks": KNOWLEDGE_BASE_CHUNKS
    }

# For backward compatibility
def load_preprocessed_knowledge_base() -> Dict[str, Any]:
    """Legacy function to load the preprocessed knowledge base."""
    return get_preprocessed_knowledge_base()

def get_knowledge_base_data() -> Dict[str, Any]:
    """
    Returns the complete knowledge base data including metadata and chunks.
    This is a pure Python implementation that doesn't rely on any external files.
    """
    return {
        "metadata": KNOWLEDGE_BASE_METADATA,
        "chunks": KNOWLEDGE_BASE_CHUNKS
    } 