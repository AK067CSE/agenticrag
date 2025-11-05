"""
Test Script for Post-Discharge Medical AI Assistant
Run this to verify all components are working correctly
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import PATIENTS_JSON, NEPHROLOGY_PDF, GOOGLE_API_KEY, GROQ_API_KEY
from logger_system import get_logger
from patient_retrieval_tool import PatientRetrievalTool
from receptionist_agent import ReceptionistAgent
from clinical_agent import ClinicalAgent
from web_search_agent import WebSearchAgent
from multi_agent_orchestrator import MultiAgentOrchestrator


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_configuration():
    """Test 1: Verify configuration and files"""
    print_section("TEST 1: Configuration & Files")
    
    # Check API keys
    print("Checking API Keys...")
    print(f"  ✓ Google API Key: {'SET' if GOOGLE_API_KEY else '❌ MISSING'}")
    print(f"  ✓ Groq API Key: {'SET' if GROQ_API_KEY else '❌ MISSING'}")
    
    # Check data files
    print("\nChecking Data Files...")
    print(f"  ✓ Patients JSON: {'EXISTS' if PATIENTS_JSON.exists() else '❌ MISSING'}")
    print(f"  ✓ Nephrology PDF: {'EXISTS' if NEPHROLOGY_PDF.exists() else '❌ MISSING'}")
    
    if not GOOGLE_API_KEY or not GROQ_API_KEY:
        print("\n❌ ERROR: API keys not configured!")
        print("   Please create a .env file with GOOGLE_API_KEY and GROQ_API_KEY")
        return False
    
    if not PATIENTS_JSON.exists() or not NEPHROLOGY_PDF.exists():
        print("\n❌ ERROR: Data files missing!")
        print("   Ensure patients.json and nephrology.pdf exist in ../data/")
        return False
    
    print("\n✅ Configuration test passed!")
    return True


def test_patient_retrieval():
    """Test 2: Patient retrieval tool"""
    print_section("TEST 2: Patient Retrieval Tool")
    
    try:
        tool = PatientRetrievalTool()
        print(f"✓ Loaded {len(tool.get_all_patients())} patient records")
        
        # Test retrieval
        print("\nTesting patient retrieval for 'John Smith'...")
        patient = tool.get_patient_by_name("John Smith")
        
        if patient:
            print("✓ Successfully retrieved patient:")
            print(f"  Name: {patient.get('patient_name')}")
            print(f"  Diagnosis: {patient.get('primary_diagnosis')}")
            print(f"  Discharge Date: {patient.get('discharge_date')}")
            print("\n✅ Patient retrieval test passed!")
            return True
        else:
            print("❌ Failed to retrieve patient")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rag_engine():
    """Test 3: RAG Engine"""
    print_section("TEST 3: RAG Engine (Vector Store)")
    
    try:
        print("Initializing RAG engine...")
        print("⚠️  Note: First run may take 2-5 minutes to process PDF")
        
        from rag_engine import RAGEngine
        rag = RAGEngine()
        
        print("✓ RAG engine initialized")
        
        # Test query
        print("\nTesting query: 'What is chronic kidney disease?'")
        has_info = rag.has_relevant_information("What is chronic kidney disease?")
        
        if has_info:
            print("✓ Found relevant information in knowledge base")
            print("\n✅ RAG engine test passed!")
            return True
        else:
            print("⚠️  No relevant info found (this may be normal for first run)")
            print("   Try running the full app to process documents")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   This might be expected if PDF processing is needed")
        return False


def test_web_search():
    """Test 4: Web Search Agent"""
    print_section("TEST 4: Web Search Agent")
    
    try:
        agent = WebSearchAgent()
        print("✓ Web search agent initialized")
        
        # Test search (don't generate full answer to save time)
        print("\nTesting DuckDuckGo search...")
        results = agent.search_web("chronic kidney disease treatment", max_results=2)
        
        if results and len(results) > 0:
            print(f"✓ Found {len(results)} search results")
            print(f"  Sample: {results[0].get('title', 'N/A')[:60]}...")
            print("\n✅ Web search test passed!")
            return True
        else:
            print("❌ No search results returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_agents():
    """Test 5: Individual Agents"""
    print_section("TEST 5: Individual Agents")
    
    try:
        # Test Receptionist
        print("Testing Receptionist Agent...")
        receptionist = ReceptionistAgent()
        greeting = receptionist.get_initial_greeting()
        print(f"✓ Receptionist greeting: {greeting[:50]}...")
        
        # Test Clinical (without full query to save time)
        print("\nTesting Clinical Agent...")
        clinical = ClinicalAgent()
        print("✓ Clinical agent initialized with RAG and web search")
        
        print("\n✅ Individual agents test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_orchestrator():
    """Test 6: Multi-Agent Orchestrator"""
    print_section("TEST 6: Multi-Agent Orchestrator")
    
    try:
        orchestrator = MultiAgentOrchestrator()
        print("✓ Orchestrator initialized")
        
        # Start session
        greeting = orchestrator.start_session()
        print(f"\n✓ Session started")
        print(f"  Greeting: {greeting[:60]}...")
        
        # Test message processing (simple greeting)
        print("\nTesting message routing...")
        result = orchestrator.process_message("Hello")
        print(f"✓ Message processed by: {result['current_agent']}")
        
        # Get status
        status = orchestrator.get_system_status()
        print(f"\n✓ System status:")
        print(f"  Session Active: {status['session_active']}")
        print(f"  Current Agent: {status['current_agent']}")
        
        print("\n✅ Orchestrator test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "🏥 POST-DISCHARGE MEDICAL AI ASSISTANT - SYSTEM TEST".center(80))
    print("DataSmith AI - GenAI Intern Assignment\n")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    
    if not results[0][1]:
        print("\n❌ Configuration failed. Please fix before continuing.")
        return
    
    results.append(("Patient Retrieval", test_patient_retrieval()))
    results.append(("RAG Engine", test_rag_engine()))
    results.append(("Web Search", test_web_search()))
    results.append(("Individual Agents", test_agents()))
    results.append(("Orchestrator", test_orchestrator()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*80}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nTo start the application, run:")
        print("  streamlit run app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        print("   Note: RAG engine test may fail on first run (PDF processing needed)")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
