"""
Post-Discharge Medical AI Assistant
Multi-Agent System for Patient Care

Modules:
- multi_agent_orchestrator: Main orchestration system
- receptionist_agent: Patient intake and routing
- clinical_agent: Medical Q&A with RAG
- web_search_agent: Web search for latest information
- rag_engine: RAG implementation with local vector stores
- patient_retrieval_tool: Patient database access
- logger_system: Comprehensive logging
- config: System configuration
"""

__version__ = "1.0.0"
__author__ = "DataSmith AI - GenAI Intern"

from .multi_agent_orchestrator import MultiAgentOrchestrator
from .receptionist_agent import ReceptionistAgent
from .clinical_agent import ClinicalAgent
from .web_search_agent import WebSearchAgent
from .rag_engine import RAGEngine
from .patient_retrieval_tool import PatientRetrievalTool
from .logger_system import get_logger

__all__ = [
    "MultiAgentOrchestrator",
    "ReceptionistAgent",
    "ClinicalAgent",
    "WebSearchAgent",
    "RAGEngine",
    "PatientRetrievalTool",
    "get_logger"
]
