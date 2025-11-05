"""
Web Search Agent - Simple Tool + LLM (version-safe)
Uses DuckDuckGo tool to fetch results, then Groq LLM to synthesize an answer
"""
import os
from typing import Dict, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Prefer community tools (newer LC); fallback to older path
try:
    from langchain_community.tools import (
        DuckDuckGoSearchResults,
        DuckDuckGoSearchRun,
    )
    _HAS_COMMUNITY = True
except Exception:  # pragma: no cover
    _HAS_COMMUNITY = False
    DuckDuckGoSearchResults = None  # type: ignore
    try:
        from langchain.tools import DuckDuckGoSearchRun  # Older LC provided this
    except Exception:  # pragma: no cover
        DuckDuckGoSearchRun = None  # type: ignore

from config import GROQ_API_KEY, GROQ_MODEL, TEMPERATURE, MEDICAL_DISCLAIMER
from logger_system import get_logger


class WebSearchAgent:
    """Perform web searches with DuckDuckGo and summarize with Groq LLM"""
    
    def __init__(self):
        """Initialize the web search agent (version-safe)"""
        self.logger = get_logger()
        self.logger.log_system_event("Initializing Web Search Agent")
        
        # Initialize DuckDuckGo tools
        if _HAS_COMMUNITY and DuckDuckGoSearchResults is not None:
            # Returns structured results (list of dicts) as a stringified summary
            self.search_tool_results = DuckDuckGoSearchResults()
        else:
            # Fallback: returns a text summary of top results
            if DuckDuckGoSearchRun is None:
                raise ImportError(
                    "DuckDuckGo tool not available. Please install langchain-community >= 0.1."
                )
            self.search_tool_results = DuckDuckGoSearchRun()
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            temperature=TEMPERATURE,
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY
        )
        
        self.logger.log_agent_action(
            "WebSearchAgent",
            "Initialized",
            {"model": GROQ_MODEL, "search_engine": "DuckDuckGo"}
        )
    
    def answer_query(self, question: str) -> Dict[str, any]:
        """
        Answer a question using DuckDuckGo + Groq LLM
        
        Args:
            question: User's question
            
        Returns:
            Dict with answer, sources, and metadata
        """
        self.logger.log_agent_action(
            "WebSearchAgent",
            "ProcessingQuery",
            {"question": question}
        )
        
        try:
            # 1) Perform web search (returns text summary for Run, JSON-like text for Results)
            search_output = self.search_tool_results.run(question)
            
            # 2) Build synthesis prompt
            prompt = PromptTemplate.from_template(
                """You are a helpful medical information assistant. Using ONLY the search results provided, 
provide a concise, accurate answer to the user's question. If the results are not relevant, say so clearly.
Always include a short list of cited URLs if present in the results and end with the medical disclaimer.

Search Results:
{search_results}

Question: {question}

Final Answer:"""
            )
            final_prompt = prompt.format(search_results=search_output, question=question)
            
            # 3) Call LLM
            answer = self.llm.invoke(final_prompt).content.strip()
            
            # Ensure medical disclaimer is included
            if MEDICAL_DISCLAIMER.strip() not in answer:
                answer += f"\n\n{MEDICAL_DISCLAIMER}"
            
            self.logger.log_agent_response("WebSearchAgent", answer)
            
            return {
                "answer": answer,
                "sources": [],  # URLs are included within the synthesized answer
                "success": True
            }
            
        except Exception as e:
            self.logger.log_error(
                "WebSearchAnswerError",
                str(e),
                {"question": question}
            )
            return {
                "answer": f"An error occurred while searching: {str(e)}. Please try rephrasing your question or consult with a healthcare professional.",
                "sources": [],
                "success": False
            }
    
    def run(self, query: str) -> str:
        """
        Main method to run web search and get answer
        
        Args:
            query: User query
            
        Returns:
            Formatted answer with sources
        """
        result = self.answer_query(query)
        
        if not result["success"]:
            return result["answer"]
        
        # Format answer with sources
        answer = result["answer"]
        
        if result["sources"]:
            answer += "\n\n**Web Sources:**\n"
            for i, source in enumerate(result["sources"], 1):
                answer += f"{i}. [{source['title']}]({source['url']})\n"
        
        return answer


# Standalone function for agent tool integration
def search_web_for_medical_info(query: str) -> str:
    """
    Search web for medical information (for agent tool use)
    
    Args:
        query: Medical query to search for
        
    Returns:
        Answer with sources and disclaimer
    """
    agent = WebSearchAgent()
    return agent.run(query)


# Test the agent
if __name__ == "__main__":
    print("Testing Web Search Agent")
    print("=" * 80)
    
    agent = WebSearchAgent()
    
    test_query = "What are the latest guidelines for managing chronic kidney disease?"
    print(f"\nQuery: {test_query}")
    print("-" * 80)
    
    answer = agent.run(test_query)
    print(f"\nAnswer:\n{answer}")
