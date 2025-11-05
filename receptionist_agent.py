"""
Receptionist Agent
- Greets patients and asks for their name
- Retrieves patient discharge reports from database
- Asks follow-up questions based on discharge information
- Routes medical queries to Clinical Agent
"""
from typing import Dict, Optional, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GROQ_API_KEY, GROQ_MODEL, TEMPERATURE
from logger_system import get_logger
from patient_retrieval_tool import PatientRetrievalTool


class ReceptionistAgent:
    """Receptionist Agent for patient intake and routing"""
    
    def __init__(self):
        self.logger = get_logger()
        self.logger.log_system_event("Initializing Receptionist Agent")
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=TEMPERATURE,
            groq_api_key=GROQ_API_KEY,
            max_tokens=2048
        )
        
        # Initialize patient retrieval tool
        self.patient_tool = PatientRetrievalTool()
        
        # Agent state
        self.current_patient = None
        self.conversation_history = []
        self.patient_name_collected = False
        
        # System instructions
        self.system_instructions = """You are a friendly and professional Receptionist Agent for a Post-Discharge Medical Care Assistant.

Your PRIMARY responsibilities:
1. Greet patients warmly and professionally
2. Ask for the patient's name if not provided
3. Use the patient database to retrieve their discharge report
4. Ask relevant follow-up questions based on their discharge information
5. Identify when patients have medical questions and route them to the Clinical Agent

Guidelines:
- Be empathetic and professional
- Ask ONE question at a time
- Confirm patient identity before discussing medical information
- When asking for a name, be clear and friendly
- After retrieving discharge info, ask about their recovery and medication compliance
- If patient asks medical questions, acknowledge and indicate you'll connect them to the Clinical Agent
- Keep responses concise and clear

Example interaction flow:
1. "Hello! I'm your post-discharge care assistant. What's your name?"
2. [After name] "Let me pull up your discharge report..."
3. [After retrieval] "Hi [Name]! I found your discharge report from [date] for [diagnosis]. How are you feeling today?"
4. [Follow-up] "Are you following your medication schedule?" 
5. [If medical question] "That's a medical question. Let me connect you with our Clinical AI Agent who can help..."

Remember:
- Always be warm and professional
- Verify patient identity
- Ask relevant follow-up questions
- Route medical queries appropriately
"""
        
        self.logger.log_agent_action(
            "ReceptionistAgent",
            "Initialized",
            {"model": GROQ_MODEL}
        )
    
    def extract_name_from_message(self, message: str) -> Optional[str]:
        """
        Attempt to extract a name from user message using LLM
        
        Args:
            message: User's message
            
        Returns:
            Extracted name or None
        """
        try:
            extraction_prompt = f"""Extract the person's name from this message. Return ONLY the name, nothing else.
If no name is present, return "NONE".

Message: "{message}"

Name:"""
            
            name = self.llm.invoke(extraction_prompt).content.strip()
            
            if name.upper() == "NONE" or len(name) > 50:
                return None
            
            return name
            
        except Exception as e:
            self.logger.log_error("NameExtraction", str(e))
            return None
    
    def retrieve_patient_info(self, patient_name: str) -> Optional[Dict]:
        """
        Retrieve patient discharge information
        
        Args:
            patient_name: Name of the patient
            
        Returns:
            Patient data dictionary or None
        """
        self.logger.log_tool_call(
            "retrieve_patient_info",
            {"patient_name": patient_name},
            None
        )
        
        patient_data = self.patient_tool.get_patient_by_name(patient_name)
        
        if patient_data:
            self.current_patient = patient_data
            self.patient_name_collected = True
            
            self.logger.log_tool_call(
                "retrieve_patient_info",
                {"patient_name": patient_name},
                {"status": "success", "patient_found": True}
            )
        
        return patient_data
    
    def should_route_to_clinical(self, message: str) -> bool:
        """
        Determine if message should be routed to Clinical Agent
        
        Args:
            message: User's message
            
        Returns:
            True if should route to clinical agent
        """
        medical_keywords = [
            "pain", "symptom", "medication", "side effect", "swelling",
            "breathing", "kidney", "diagnosis", "treatment", "disease",
            "should i", "is it normal", "worried", "concern", "doctor",
            "medical", "health", "blood", "urine", "diet", "exercise"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in medical_keywords)
    
    def process_message(self, user_message: str) -> Dict:
        """
        Process user message and generate appropriate response
        
        Args:
            user_message: User's input message
            
        Returns:
            Dict with response, action, and metadata
        """
        self.logger.log_user_message(user_message)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Check if we need to route to clinical agent
            if self.patient_name_collected and self.should_route_to_clinical(user_message):
                self.logger.log_agent_handoff(
                    "ReceptionistAgent",
                    "ClinicalAgent",
                    f"Medical query detected: {user_message[:50]}..."
                )
                
                return {
                    "response": "I understand you have a medical question. Let me connect you with our Clinical AI Agent who can provide detailed medical information.",
                    "action": "route_to_clinical",
                    "route_to": "clinical",
                    "original_query": user_message,
                    "patient_context": self.current_patient
                }
            
            # If patient name not collected, try to extract it
            if not self.patient_name_collected:
                name = self.extract_name_from_message(user_message)
                
                if name:
                    # Try to retrieve patient info
                    patient_data = self.retrieve_patient_info(name)
                    
                    if patient_data:
                        # Handle multiple matches warning
                        if "warning" in patient_data:
                            warning = patient_data["warning"]
                            patient_data = patient_data["patient"]
                            formatted_info = self.patient_tool.format_patient_info({"warning": warning, "patient": patient_data})
                        else:
                            formatted_info = self.patient_tool.format_patient_info(patient_data)
                        
                        # Generate personalized greeting
                        context = f"""Patient discharge information:
{formatted_info}

Generate a warm, professional greeting that:
1. Confirms you found their discharge report
2. Mentions the discharge date and primary diagnosis
3. Asks how they're feeling today
4. Keep it conversational and brief (2-3 sentences)"""
                        
                        greeting = self.llm.invoke(context).content.strip()
                        
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": greeting
                        })
                        
                        self.logger.log_agent_response("ReceptionistAgent", greeting)
                        
                        return {
                            "response": greeting,
                            "action": "patient_retrieved",
                            "patient_data": patient_data,
                            "route_to": None
                        }
                    else:
                        # Patient not found
                        response = f"I couldn't find a discharge report for '{name}'. Could you please verify the spelling of your name?"
                        
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        
                        return {
                            "response": response,
                            "action": "patient_not_found",
                            "route_to": None
                        }
            
            # Generate contextual response
            context = self._build_context()
            prompt = f"""{self.system_instructions}

{context}

User: {user_message}

Generate an appropriate response following your role as Receptionist Agent."""
            
            agent_response = self.llm.invoke(prompt).content.strip()
            
            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })
            
            self.logger.log_agent_response("ReceptionistAgent", agent_response)
            
            return {
                "response": agent_response,
                "action": "conversation",
                "route_to": None
            }
            
        except Exception as e:
            self.logger.log_error("ReceptionistProcessing", str(e))
            error_response = "I apologize, I encountered an error. Could you please repeat that?"
            
            return {
                "response": error_response,
                "action": "error",
                "route_to": None,
                "error": str(e)
            }
    
    def _build_context(self) -> str:
        """Build conversation context"""
        context_parts = []
        
        if self.current_patient:
            patient_info = self.patient_tool.format_patient_info(self.current_patient)
            context_parts.append(f"Current Patient Information:\n{patient_info}")
        
        if self.conversation_history:
            recent_history = self.conversation_history[-5:]  # Last 5 exchanges
            history_str = "\n".join([
                f"{msg['role'].title()}: {msg['content']}"
                for msg in recent_history
            ])
            context_parts.append(f"\nConversation History:\n{history_str}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def reset(self):
        """Reset agent state for new conversation"""
        self.current_patient = None
        self.conversation_history = []
        self.patient_name_collected = False
        self.logger.log_system_event("Receptionist Agent reset for new conversation")
    
    def get_initial_greeting(self) -> str:
        """Get the initial greeting message"""
        greeting = """Hello! 👋 I'm your Post-Discharge Care Assistant.

I'm here to help you with your recovery after your hospital discharge.

**What's your name?**"""
        
        self.logger.log_agent_response("ReceptionistAgent", greeting)
        return greeting


# Test the agent
if __name__ == "__main__":
    print("Testing Receptionist Agent")
    print("=" * 80)
    
    agent = ReceptionistAgent()
    
    # Test 1: Initial greeting
    print("\n1. Initial Greeting:")
    print(agent.get_initial_greeting())
    
    # Test 2: Provide name
    print("\n2. User provides name:")
    result = agent.process_message("My name is John Smith")
    print(f"Response: {result['response']}")
    print(f"Action: {result['action']}")
    
    # Test 3: Medical question
    print("\n3. User asks medical question:")
    result = agent.process_message("I'm having swelling in my legs. Should I be worried?")
    print(f"Response: {result['response']}")
    print(f"Action: {result['action']}")
    print(f"Route to: {result.get('route_to')}")
