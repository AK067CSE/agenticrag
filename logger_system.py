"""
Comprehensive Logging System for Multi-Agent Medical Assistant
Logs all interactions, agent handoffs, and system events
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from config import LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT


class MedicalAssistantLogger:
    """Centralized logging system for the medical assistant"""
    
    def __init__(self, log_dir: Path = LOGS_DIR):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"medical_assistant_{timestamp}.log"
        
        # Setup main logger
        self.logger = logging.getLogger("MedicalAssistant")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 80)
        self.logger.info("Medical Assistant Logging System Initialized")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info("=" * 80)
    
    def log_user_message(self, message: str, session_id: Optional[str] = None):
        """Log user input message"""
        session_info = f"[Session: {session_id}] " if session_id else ""
        self.logger.info(f"{session_info}USER INPUT: {message}")
    
    def log_agent_action(self, agent_name: str, action: str, details: Optional[dict] = None):
        """Log agent actions"""
        details_str = json.dumps(details, indent=2) if details else ""
        self.logger.info(f"[{agent_name}] ACTION: {action}")
        if details_str:
            self.logger.debug(f"[{agent_name}] DETAILS: {details_str}")
    
    def log_agent_response(self, agent_name: str, response: str):
        """Log agent responses"""
        self.logger.info(f"[{agent_name}] RESPONSE: {response[:200]}...")
    
    def log_agent_handoff(self, from_agent: str, to_agent: str, reason: str):
        """Log agent handoff events"""
        self.logger.info(f"🔄 AGENT HANDOFF: {from_agent} → {to_agent}")
        self.logger.info(f"   Reason: {reason}")
    
    def log_tool_call(self, tool_name: str, parameters: dict, result: Optional[dict] = None):
        """Log tool invocations"""
        self.logger.info(f"🔧 TOOL CALL: {tool_name}")
        self.logger.debug(f"   Parameters: {json.dumps(parameters, indent=2)}")
        if result:
            self.logger.debug(f"   Result: {json.dumps(result, indent=2)}")
    
    def log_rag_retrieval(self, query: str, num_docs: int, sources: list):
        """Log RAG document retrieval"""
        self.logger.info(f"📚 RAG RETRIEVAL: Query='{query}', Retrieved {num_docs} documents")
        self.logger.debug(f"   Sources: {sources}")
    
    def log_web_search(self, query: str, num_results: int):
        """Log web search events"""
        self.logger.info(f"🌐 WEB SEARCH: Query='{query}', Results={num_results}")
    
    def log_error(self, error_type: str, error_msg: str, context: Optional[dict] = None):
        """Log errors with context"""
        self.logger.error(f"❌ ERROR [{error_type}]: {error_msg}")
        if context:
            self.logger.error(f"   Context: {json.dumps(context, indent=2)}")
    
    def log_session_start(self, session_id: str):
        """Log session start"""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 NEW SESSION STARTED: {session_id}")
        self.logger.info("=" * 80)
    
    def log_session_end(self, session_id: str):
        """Log session end"""
        self.logger.info("=" * 80)
        self.logger.info(f"✅ SESSION ENDED: {session_id}")
        self.logger.info("=" * 80)
    
    def log_system_event(self, event: str, details: Optional[str] = None):
        """Log general system events"""
        self.logger.info(f"⚙️ SYSTEM: {event}")
        if details:
            self.logger.debug(f"   {details}")


# Global logger instance
_logger_instance = None

def get_logger() -> MedicalAssistantLogger:
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = MedicalAssistantLogger()
    return _logger_instance
