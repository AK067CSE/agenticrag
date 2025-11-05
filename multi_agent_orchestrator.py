"""
Multi-Agent Orchestrator
Coordinates between Receptionist Agent, Clinical Agent, and Web Search Agent
Manages conversation flow and agent handoffs
"""
from typing import Dict, List, Optional
from enum import Enum

from logger_system import get_logger
from receptionist_agent import ReceptionistAgent
from clinical_agent import ClinicalAgent
from web_search_agent import WebSearchAgent


class AgentType(Enum):
    """Enum for different agent types"""
    RECEPTIONIST = "receptionist"
    CLINICAL = "clinical"
    WEB_SEARCH = "web_search"


class MultiAgentOrchestrator:
    """
    Orchestrator for managing multiple AI agents in the medical assistant system
    
    Workflow:
    1. All conversations start with Receptionist Agent
    2. Receptionist collects patient name and retrieves discharge info
    3. Receptionist routes medical questions to Clinical Agent
    4. Clinical Agent uses RAG or falls back to Web Search Agent
    5. Responses are logged and tracked throughout
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.logger.log_system_event("Initializing Multi-Agent Orchestrator")
        
        # Initialize all agents
        self.receptionist_agent = ReceptionistAgent()
        self.clinical_agent = ClinicalAgent()
        self.web_search_agent = WebSearchAgent()
        
        # State management
        self.current_agent = AgentType.RECEPTIONIST
        self.session_active = False
        self.patient_context = None
        self.conversation_log = []
        
        self.logger.log_system_event(
            "Multi-Agent Orchestrator initialized",
            f"Available agents: {[agent.value for agent in AgentType]}"
        )
    
    def start_session(self) -> str:
        """
        Start a new conversation session
        
        Returns:
            Initial greeting from Receptionist Agent
        """
        self.session_active = True
        self.current_agent = AgentType.RECEPTIONIST
        
        session_id = f"session_{id(self)}"
        self.logger.log_session_start(session_id)
        
        # Get initial greeting from receptionist
        greeting = self.receptionist_agent.get_initial_greeting()
        
        self._log_interaction(
            agent=AgentType.RECEPTIONIST,
            message_type="greeting",
            content=greeting
        )
        
        return greeting
    
    def process_message(self, user_message: str) -> Dict:
        """
        Process user message and route to appropriate agent
        
        Args:
            user_message: User's input message
            
        Returns:
            Dict containing:
                - response: Agent's response
                - current_agent: Which agent generated the response
                - action: What action was taken
                - metadata: Additional information
        """
        if not self.session_active:
            return {
                "response": "Please start a new session first.",
                "current_agent": None,
                "action": "error",
                "metadata": {}
            }
        
        self.logger.log_user_message(user_message)
        
        self._log_interaction(
            agent=self.current_agent,
            message_type="user_input",
            content=user_message
        )
        
        try:
            # Route based on current agent
            if self.current_agent == AgentType.RECEPTIONIST:
                return self._handle_receptionist_flow(user_message)
            
            elif self.current_agent == AgentType.CLINICAL:
                return self._handle_clinical_flow(user_message)
            
            else:
                # Should not reach here in normal flow
                return {
                    "response": "I'm not sure how to help with that. Let me start over.",
                    "current_agent": self.current_agent.value,
                    "action": "reset",
                    "metadata": {}
                }
        
        except Exception as e:
            self.logger.log_error("MessageProcessing", str(e), {"user_message": user_message})
            return {
                "response": "I apologize, I encountered an error. Please try again.",
                "current_agent": self.current_agent.value if self.current_agent else None,
                "action": "error",
                "metadata": {"error": str(e)}
            }
    
    def _handle_receptionist_flow(self, user_message: str) -> Dict:
        """Handle message when Receptionist Agent is active"""
        
        result = self.receptionist_agent.process_message(user_message)
        
        # Check if routing is needed
        if result.get("action") == "route_to_clinical":
            # Switch to Clinical Agent
            self.current_agent = AgentType.CLINICAL
            self.patient_context = result.get("patient_context")
            
            self.logger.log_agent_handoff(
                "ReceptionistAgent",
                "ClinicalAgent",
                f"Medical query: {result.get('original_query', '')[:50]}..."
            )
            
            # Process the medical query with Clinical Agent
            clinical_result = self.clinical_agent.process_medical_query(
                result.get("original_query"),
                self.patient_context
            )
            
            response = f"{result['response']}\n\n---\n\n{clinical_result['answer']}"
            
            self._log_interaction(
                agent=AgentType.CLINICAL,
                message_type="response",
                content=response,
                metadata={
                    "source_type": clinical_result.get("source_type"),
                    "sources_count": len(clinical_result.get("sources", []))
                }
            )
            
            return {
                "response": response,
                "current_agent": AgentType.CLINICAL.value,
                "action": "clinical_response",
                "metadata": {
                    "source_type": clinical_result.get("source_type"),
                    "sources": clinical_result.get("sources", []),
                    "patient_context": self.patient_context
                }
            }
        
        # Store patient context if retrieved
        if result.get("action") == "patient_retrieved":
            self.patient_context = result.get("patient_data")
        
        self._log_interaction(
            agent=AgentType.RECEPTIONIST,
            message_type="response",
            content=result["response"],
            metadata={"action": result.get("action")}
        )
        
        return {
            "response": result["response"],
            "current_agent": AgentType.RECEPTIONIST.value,
            "action": result.get("action"),
            "metadata": {
                "patient_context": self.patient_context
            }
        }
    
    def _handle_clinical_flow(self, user_message: str) -> Dict:
        """Handle message when Clinical Agent is active"""
        
        # Check if user wants to go back to receptionist
        if any(phrase in user_message.lower() for phrase in ["go back", "receptionist", "start over", "new patient"]):
            self.current_agent = AgentType.RECEPTIONIST
            self.patient_context = None
            self.receptionist_agent.reset()
            self.clinical_agent.reset()
            
            self.logger.log_agent_handoff(
                "ClinicalAgent",
                "ReceptionistAgent",
                "User requested to return to receptionist"
            )
            
            response = "Returning to reception. How can I help you?"
            
            return {
                "response": response,
                "current_agent": AgentType.RECEPTIONIST.value,
                "action": "return_to_receptionist",
                "metadata": {}
            }
        
        # Process medical query
        result = self.clinical_agent.process_medical_query(
            user_message,
            self.patient_context
        )
        
        self._log_interaction(
            agent=AgentType.CLINICAL,
            message_type="response",
            content=result["answer"],
            metadata={
                "source_type": result.get("source_type"),
                "sources_count": len(result.get("sources", []))
            }
        )
        
        return {
            "response": result["answer"],
            "current_agent": AgentType.CLINICAL.value,
            "action": "clinical_response",
            "metadata": {
                "source_type": result.get("source_type"),
                "sources": result.get("sources", []),
                "success": result.get("success")
            }
        }
    
    def _log_interaction(
        self,
        agent: AgentType,
        message_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Log an interaction to the conversation log"""
        interaction = {
            "agent": agent.value if isinstance(agent, AgentType) else agent,
            "message_type": message_type,
            "content": content,
            "metadata": metadata or {}
        }
        self.conversation_log.append(interaction)
    
    def get_conversation_log(self) -> List[Dict]:
        """Get the complete conversation log"""
        return self.conversation_log
    
    def get_current_agent(self) -> Optional[str]:
        """Get the currently active agent"""
        return self.current_agent.value if self.current_agent else None
    
    def get_patient_context(self) -> Optional[Dict]:
        """Get the current patient context"""
        return self.patient_context
    
    def reset_session(self):
        """Reset the entire session"""
        self.logger.log_session_end(f"session_{id(self)}")
        
        self.session_active = False
        self.current_agent = AgentType.RECEPTIONIST
        self.patient_context = None
        self.conversation_log = []
        
        # Reset all agents
        self.receptionist_agent.reset()
        self.clinical_agent.reset()
        
        self.logger.log_system_event("Session reset complete")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "session_active": self.session_active,
            "current_agent": self.current_agent.value if self.current_agent else None,
            "patient_identified": self.patient_context is not None,
            "patient_name": self.patient_context.get("patient_name") if self.patient_context else None,
            "conversation_length": len(self.conversation_log)
        }


# Test the orchestrator
if __name__ == "__main__":
    print("Testing Multi-Agent Orchestrator")
    print("=" * 80)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Start session
    print("\n1. Starting session:")
    greeting = orchestrator.start_session()
    print(f"Greeting: {greeting}")
    print(f"Current Agent: {orchestrator.get_current_agent()}")
    
    # User provides name
    print("\n2. User provides name:")
    result = orchestrator.process_message("My name is John Smith")
    print(f"Response: {result['response'][:200]}...")
    print(f"Current Agent: {result['current_agent']}")
    print(f"Action: {result['action']}")
    
    # User asks medical question
    print("\n3. User asks medical question:")
    result = orchestrator.process_message("I'm having swelling in my legs. Is this normal?")
    print(f"Current Agent: {result['current_agent']}")
    print(f"Action: {result['action']}")
    print(f"Source Type: {result['metadata'].get('source_type')}")
    print(f"Response Preview: {result['response'][:200]}...")
    
    # Get system status
    print("\n4. System Status:")
    status = orchestrator.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Get conversation log summary
    print(f"\n5. Conversation Log: {len(orchestrator.get_conversation_log())} interactions")
