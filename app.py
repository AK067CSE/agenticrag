"""
Streamlit Application for Post Discharge Medical AI Assistant
Multi-Agent System with Receptionist, Clinical, and Web Search Agents
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from multi_agent_orchestrator import MultiAgentOrchestrator, AgentType
from config import MEDICAL_DISCLAIMER, VECTOR_STORE_TYPE
from logger_system import get_logger


# Page configuration
st.set_page_config(
    page_title="Post-Discharge Care Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .receptionist-badge {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .clinical-badge {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .web-search-badge {
        background-color: #e8f5e9;
        color: #388e3c;
    }
    .patient-info-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .disclaimer-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .source-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = MultiAgentOrchestrator()
        st.session_state.logger = get_logger()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'session_started' not in st.session_state:
        st.session_state.session_started = False
    
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = None


def render_agent_badge(agent_name: str):
    """Render agent badge with appropriate styling"""
    badge_class = {
        "receptionist": "receptionist-badge",
        "clinical": "clinical-badge",
        "web_search": "web-search-badge"
    }.get(agent_name, "receptionist-badge")
    
    display_name = {
        "receptionist": "🏨 Receptionist",
        "clinical": "⚕️ Clinical AI",
        "web_search": "🌐 Web Search"
    }.get(agent_name, "🤖 Assistant")
    
    return f'<span class="agent-badge {badge_class}">{display_name}</span>'


def render_message(role: str, content: str, agent_name: str = None, metadata: dict = None):
    """Render a chat message with appropriate styling"""
    
    with st.chat_message(role):
        # Show agent badge for assistant messages
        if role == "assistant" and agent_name:
            st.markdown(render_agent_badge(agent_name), unsafe_allow_html=True)
        
        # Show message content
        st.markdown(content)
        
        # Show metadata if available
        if metadata and role == "assistant":
            # Show source information
            if metadata.get("source_type"):
                source_type = metadata["source_type"]
                
                if source_type == "nephrology_knowledge_base":
                    sources = metadata.get("sources", [])
                    if sources:
                        st.markdown(f"""
                        <div class="source-box">
                            📚 <strong>Source:</strong> Nephrology Knowledge Base<br>
                            <strong>References:</strong> {len(sources)} document(s) with relevance scores
                        </div>
                        """, unsafe_allow_html=True)
                
                elif source_type == "web_search":
                    sources = metadata.get("sources", [])
                    if sources:
                        with st.expander("🌐 View Web Sources"):
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"{i}. [{source.get('title', 'N/A')}]({source.get('url', '#')})")
            
            # Show patient context indicator
            if metadata.get("patient_context"):
                patient = metadata["patient_context"]
                if "warning" in patient:
                    patient = patient["patient"]
                
                with st.expander("📋 Patient Context Applied"):
                    st.markdown(f"""
                    - **Name:** {patient.get('patient_name', 'N/A')}
                    - **Diagnosis:** {patient.get('primary_diagnosis', 'N/A')}
                    - **Discharge Date:** {patient.get('discharge_date', 'N/A')}
                    """)


def main():
    """Main application function"""
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🏥 Post-Discharge Care Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Multi-Agent Medical Support System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ System Information")
        
        # System status
        if st.session_state.session_started:
            status = st.session_state.orchestrator.get_system_status()
            
            st.success("✅ Session Active")
            
            st.metric("Current Agent", status.get("current_agent", "N/A").title())
            st.metric("Conversation Length", status.get("conversation_length", 0))
            
            if status.get("patient_identified"):
                st.info(f"👤 Patient: {status.get('patient_name', 'N/A')}")
        else:
            st.warning("⏸️ Session Not Started")
        
        st.divider()
        
        # System Configuration
        st.header("⚙️ Configuration")
        st.info(f"**Vector Store:** {VECTOR_STORE_TYPE.upper()}")
        st.info("**Agents Active:** 3")
        st.markdown("""
        - 🏨 Receptionist Agent
        - ⚕️ Clinical AI Agent  
        - 🌐 Web Search Agent
        """)
        
        st.divider()
        
        # Session controls
        st.header("🎮 Session Controls")
        
        if not st.session_state.session_started:
            if st.button("🚀 Start New Session", use_container_width=True, type="primary"):
                greeting = st.session_state.orchestrator.start_session()
                st.session_state.session_started = True
                st.session_state.session_start_time = datetime.now()
                
                # Add greeting to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": greeting,
                    "agent": "receptionist",
                    "metadata": {}
                })
                
                st.rerun()
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Reset Session", use_container_width=True):
                    st.session_state.orchestrator.reset_session()
                    st.session_state.messages = []
                    st.session_state.session_started = False
                    st.session_state.session_start_time = None
                    st.rerun()
            
            with col2:
                if st.button("📥 Download Log", use_container_width=True):
                    log = st.session_state.orchestrator.get_conversation_log()
                    st.download_button(
                        "Save Conversation",
                        data=str(log),
                        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        st.divider()
        
        # Information
        st.header("📖 About")
        st.markdown("""
        This AI assistant helps patients with post-discharge care by:
        
        - 📋 Accessing discharge reports
        - 💊 Answering medication questions
        - 🩺 Providing medical information
        - 🔍 Searching medical databases
        
        **Data Sources:**
        - Patient Database (25+ records)
        - Nephrology Knowledge Base
        - Real-time Web Search
        """)
        
        # Medical Disclaimer
        st.divider()
        st.markdown(f'<div class="disclaimer-box">{MEDICAL_DISCLAIMER}</div>', unsafe_allow_html=True)
    
    # Main chat area
    if not st.session_state.session_started:
        # Welcome screen
        st.info("👈 Click '🚀 Start New Session' in the sidebar to begin")
        
        st.markdown("""
        ### How It Works
        
        1. **Start a Session** - Click the button to begin
        2. **Provide Your Name** - The receptionist will ask for your name
        3. **View Your Report** - Your discharge information will be retrieved
        4. **Ask Questions** - Get answers from our AI medical assistant
        5. **Get Help** - Medical questions are routed to specialized agents
        
        ### Features
        
        - 🤖 **Multi-Agent System** - Specialized agents for different tasks
        - 📚 **Knowledge Base** - Nephrology reference materials
        - 🌐 **Web Search** - Fallback for latest information
        - 📝 **Comprehensive Logging** - All interactions are tracked
        - 🔒 **Privacy Focused** - Local vector storage (ChromaDB/FAISS)
        """)
    
    else:
        # Display chat messages
        for message in st.session_state.messages:
            render_message(
                message["role"],
                message["content"],
                message.get("agent"),
                message.get("metadata")
            )
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "agent": None,
                "metadata": {}
            })
            
            # Display user message
            render_message("user", prompt)
            
            # Process message through orchestrator
            with st.spinner("Processing..."):
                result = st.session_state.orchestrator.process_message(prompt)
            
            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "agent": result.get("current_agent"),
                "metadata": result.get("metadata", {})
            })
            
            # Display assistant response
            render_message(
                "assistant",
                result["response"],
                result.get("current_agent"),
                result.get("metadata")
            )
            
            # Show action notification if needed
            action = result.get("action")
            if action == "patient_retrieved":
                st.toast("✅ Patient record retrieved successfully!", icon="✅")
            elif action == "route_to_clinical":
                st.toast("🔄 Routing to Clinical AI Agent...", icon="🔄")
            elif action == "clinical_response":
                source_type = result.get("metadata", {}).get("source_type")
                if source_type == "nephrology_knowledge_base":
                    st.toast("📚 Answer from Knowledge Base", icon="📚")
                elif source_type == "web_search":
                    st.toast("🌐 Answer from Web Search", icon="🌐")


if __name__ == "__main__":
    main()
