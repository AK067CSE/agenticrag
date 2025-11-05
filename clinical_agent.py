"""
Clinical AI Agent
- Handles medical questions and clinical advice
- Uses RAG over nephrology reference book for answers
- Falls back to web search when RAG doesn't have information
- Provides citations from reference materials
- Logs all interactions
"""
from typing import Dict, Optional, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import (
    GROQ_API_KEY, GROQ_MODEL, TEMPERATURE,
    SIMILARITY_THRESHOLD, TOP_K_RESULTS, MEDICAL_DISCLAIMER
)
from logger_system import get_logger
# Use fast RAG engine for better performance
from rag_engine_fast import get_rag_engine, get_context_for_query, has_relevant_information
from web_search_agent import WebSearchAgent


class ClinicalAgent:
    """Clinical AI Agent for medical queries with RAG and web search"""
    
    def __init__(self):
        self.logger = get_logger()
        self.logger.log_system_event("Initializing Clinical AI Agent")
        
        # Initialize Groq LLM for RAG
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=TEMPERATURE,
            groq_api_key=GROQ_API_KEY,
            max_tokens=2048
        )
        
        # Initialize RAG engine (uses singleton pattern)
        self.rag_engine = get_rag_engine()
        
        # Initialize web search agent
        self.web_search_agent = WebSearchAgent()
        
        # Conversation history
        self.conversation_history = []
        
        # System instructions
        self.system_instructions = """You are a specialized Clinical AI Agent providing medical information for post-discharge patient care.

Your PRIMARY responsibilities:
1. Answer medical questions using the nephrology knowledge base
2. Provide evidence-based clinical information
3. Always cite your sources
4. Use web search when knowledge base lacks information
5. Include appropriate medical disclaimers

Guidelines:
- Be professional and accurate
- Explain medical concepts clearly
- Always cite sources from the knowledge base or web
- If uncertain, state limitations clearly
- Prioritize patient safety in all responses
- Use medical terminology but explain it for patients
- Acknowledge when questions are outside your scope

Response Structure:
1. Direct answer to the question
2. Supporting details from sources
3. Practical advice if applicable
4. Source citations
5. Medical disclaimer

Important:
- Never provide diagnoses
- Never replace professional medical advice
- Always emphasize consulting healthcare providers
- Be clear about information sources (knowledge base vs web search)
"""
        
        # Create RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_instructions),
            ("human", "{context}\n\nPatient Context: {patient_context}\n\nQuestion: {question}")
        ])
        
        # Create RAG chain
        self.rag_chain = self.rag_prompt | self.llm | StrOutputParser()
        
        self.logger.log_agent_action(
            "ClinicalAgent",
            "Initialized",
            {"model": GROQ_MODEL, "rag_enabled": True, "web_search_enabled": True}
        )
    
    def process_medical_query(
        self,
        query: str,
        patient_context: Optional[Dict] = None
    ) -> Dict:
        """
        Process a medical query using RAG and optionally web search
        
        Args:
            query: Medical question from patient
            patient_context: Optional patient discharge information
            
        Returns:
            Dict with answer, sources, and metadata
        """
        self.logger.log_user_message(query)
        self.logger.log_agent_action(
            "ClinicalAgent",
            "ProcessingMedicalQuery",
            {"query": query[:100], "has_patient_context": patient_context is not None}
        )
        
        try:
            # Step 1: Try RAG first (using fast retrieval)
            rag_context = self.rag_engine.get_context_for_query(
                query,
                k=TOP_K_RESULTS
            )
            
            if rag_context:
                # Use RAG results
                return self._generate_rag_answer(query, rag_context, patient_context)
            else:
                # Fallback to web search
                self.logger.log_agent_action(
                    "ClinicalAgent",
                    "RAGNoResults",
                    {"query": query, "action": "falling_back_to_web_search"}
                )
                return self._generate_web_search_answer(query, patient_context)
        
        except Exception as e:
            self.logger.log_error("ClinicalQueryProcessing", str(e), {"query": query})
            return {
                "answer": "I apologize, I encountered an error processing your question. Please try rephrasing or consult with your healthcare provider.",
                "sources": [],
                "source_type": "error",
                "success": False,
                "error": str(e)
            }
    
    def _generate_rag_answer(
        self,
        query: str,
        rag_context: str,
        patient_context: Optional[Dict]
    ) -> Dict:
        """Generate answer using RAG context"""
        
        self.logger.log_agent_action(
            "ClinicalAgent",
            "GeneratingRAGAnswer",
            {"query": query[:100]}
        )
        
        # Build patient context string
        patient_info = "None provided"
        if patient_context:
            if "warning" in patient_context:
                patient_context = patient_context["patient"]
            
            patient_info = f"""Name: {patient_context.get('patient_name', 'N/A')}
Diagnosis: {patient_context.get('primary_diagnosis', 'N/A')}
Medications: {', '.join(patient_context.get('medications', []))}
Dietary Restrictions: {patient_context.get('dietary_restrictions', 'N/A')}"""
        
        try:
            # Use Groq LLM chain for RAG answer
            answer = self.rag_chain.invoke({
                "context": rag_context,
                "patient_context": patient_info,
                "question": query
            })
            
            # Ensure disclaimer is included
            if MEDICAL_DISCLAIMER.strip() not in answer:
                answer += f"\n\n{MEDICAL_DISCLAIMER}"
            
            self.logger.log_agent_response("ClinicalAgent", answer)
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": query
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": answer,
                "source_type": "rag"
            })
            
            return {
                "answer": answer,
                "sources": self._extract_rag_sources(rag_context),
                "source_type": "nephrology_knowledge_base",
                "success": True
            }
            
        except Exception as e:
            self.logger.log_error("RAGAnswerGeneration", str(e))
            raise
    
    def _generate_web_search_answer(
        self,
        query: str,
        patient_context: Optional[Dict]
    ) -> Dict:
        """Generate answer using web search"""
        
        self.logger.log_agent_handoff(
            "ClinicalAgent",
            "WebSearchAgent",
            f"No relevant information in knowledge base for: {query[:50]}..."
        )
        
        # Use web search agent
        web_result = self.web_search_agent.answer_query(query)
        
        if not web_result["success"]:
            return {
                "answer": web_result["answer"],
                "sources": [],
                "source_type": "web_search_failed",
                "success": False
            }
        
        # Enhance answer with patient context if available
        answer = web_result["answer"]
        
        if patient_context:
            if "warning" in patient_context:
                patient_context = patient_context["patient"]
            
            enhancement_prompt = f"""Given this web search answer about: "{query}"

Answer:
{answer}

Patient Context:
- Diagnosis: {patient_context.get('primary_diagnosis', 'N/A')}
- Medications: {', '.join(patient_context.get('medications', []))}
- Dietary Restrictions: {patient_context.get('dietary_restrictions', 'N/A')}

Add a brief personalized note (1-2 sentences) relating the answer to this patient's specific condition.
Keep the original answer intact, just add the personalized note at the end before the disclaimer."""
            
            try:
                # Use Groq LLM to enhance answer with patient context
                enhanced = self.llm.invoke(enhancement_prompt).content.strip()
                answer = enhanced
                
                if MEDICAL_DISCLAIMER.strip() not in answer:
                    answer += f"\n\n{MEDICAL_DISCLAIMER}"
                    
            except Exception as e:
                self.logger.log_error("AnswerEnhancement", str(e))
        
        self.logger.log_agent_response("ClinicalAgent", answer)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": answer,
            "source_type": "web_search"
        })
        
        return {
            "answer": answer,
            "sources": web_result["sources"],
            "source_type": "web_search",
            "success": True
        }
    
    def _extract_rag_sources(self, rag_context: str) -> List[Dict]:
        """Extract source information from RAG context"""
        sources = []
        
        # Parse source citations from context
        import re
        source_pattern = r'\[Source (\d+) - Page ([\d\w]+), Relevance: ([\d.]+)\]'
        matches = re.finditer(source_pattern, rag_context)
        
        for match in matches:
            sources.append({
                "source_number": match.group(1),
                "page": match.group(2),
                "relevance": float(match.group(3)),
                "type": "nephrology_textbook"
            })
        
        return sources
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return self.conversation_history
    
    def reset(self):
        """Reset agent state for new conversation"""
        self.conversation_history = []
        self.logger.log_system_event("Clinical Agent reset for new conversation")
    
    def check_knowledge_base_coverage(self, query: str) -> bool:
        """
        Check if knowledge base has information about query
        
        Args:
            query: Search query
            
        Returns:
            True if knowledge base has relevant info
        """
        return self.rag_engine.has_relevant_information(
            query, 
            threshold=SIMILARITY_THRESHOLD
        )


# Standalone function for testing
def answer_medical_question(question: str, patient_context: Optional[Dict] = None) -> str:
    """
    Answer a medical question (for testing)
    
    Args:
        question: Medical question
        patient_context: Optional patient information
        
    Returns:
        Answer string
    """
    agent = ClinicalAgent()
    result = agent.process_medical_query(question, patient_context)
    
    answer = result["answer"]
    
    # Add source information
    if result.get("sources"):
        answer += f"\n\n**Information Source:** {result['source_type']}"
        
        if result["source_type"] == "nephrology_knowledge_base":
            answer += f"\n**Knowledge Base Sources:** {len(result['sources'])} references"
        elif result["source_type"] == "web_search":
            answer += "\n**Web Sources:**\n"
            for i, source in enumerate(result["sources"], 1):
                answer += f"{i}. {source['title']}\n"
    
    return answer


# Test the agent
if __name__ == "__main__":
    print("Testing Clinical AI Agent")
    print("=" * 80)
    
    agent = ClinicalAgent()
    
    # Test 1: Query that should use RAG
    print("\n1. Testing RAG Query:")
    query1 = "What is chronic kidney disease?"
    result1 = agent.process_medical_query(query1)
    print(f"Query: {query1}")
    print(f"Source Type: {result1['source_type']}")
    print(f"Answer Preview: {result1['answer'][:200]}...")
    
    # Test 2: Query that might need web search
    print("\n2. Testing Web Search Fallback:")
    query2 = "What are the latest SGLT2 inhibitors for CKD treatment in 2024?"
    result2 = agent.process_medical_query(query2)
    print(f"Query: {query2}")
    print(f"Source Type: {result2['source_type']}")
    print(f"Answer Preview: {result2['answer'][:200]}...")
    
    # Test 3: Query with patient context
    print("\n3. Testing with Patient Context:")
    patient_ctx = {
        "patient_name": "John Smith",
        "primary_diagnosis": "Chronic Kidney Disease Stage 3",
        "medications": ["Lisinopril 10mg daily"],
        "dietary_restrictions": "Low sodium"
    }
    query3 = "Can I eat high-potassium foods?"
    result3 = agent.process_medical_query(query3, patient_ctx)
    print(f"Query: {query3}")
    print(f"Source Type: {result3['source_type']}")
    print(f"Answer Preview: {result3['answer'][:200]}...")
