#!/usr/bin/env python3
"""
Quick Setup Script for Advanced RAG System
Checks prerequisites and runs initial setup
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def check_file(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: Found")
        return True
    else:
        print(f"❌ {description}: NOT FOUND at {filepath}")
        return False

def check_env_variable(var_name):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        masked = value[:8] + "..." if len(value) > 8 else value
        print(f"✅ {var_name}: Set ({masked})")
        return True
    else:
        print(f"❌ {var_name}: NOT SET")
        return False

def main():
    """Main setup check"""
    print_header("Post-Discharge AI Assistant - Setup Checker")
    
    all_checks_passed = True
    
    # Check 1: Python version
    print("🐍 Python Version Check")
    py_version = sys.version_info
    if py_version.major >= 3 and py_version.minor >= 8:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"❌ Python {py_version.major}.{py_version.minor} (need 3.8+)")
        all_checks_passed = False
    
    # Check 2: Required files
    print("\n📁 File Check")
    files_ok = True
    files_ok &= check_file("../data/nephrology.pdf", "Nephrology PDF")
    files_ok &= check_file(".env", ".env file")
    files_ok &= check_file("requirements.txt", "Requirements")
    
    if not files_ok:
        all_checks_passed = False
    
    # Check 3: Environment variables
    print("\n🔑 API Keys Check")
    env_ok = True
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed yet")
    
    env_ok &= check_env_variable("GEMINI_API_KEY")
    env_ok &= check_env_variable("GROQ_API_KEY")
    
    if not env_ok:
        all_checks_passed = False
        print("\n💡 Add your API keys to the .env file:")
        print("   GEMINI_API_KEY=your_key_here")
        print("   GROQ_API_KEY=your_key_here")
    
    # Check 4: Dependencies
    print("\n📦 Dependencies Check")
    try:
        import streamlit
        print("✅ streamlit")
    except ImportError:
        print("❌ streamlit - run: pip install -r requirements.txt")
        all_checks_passed = False
    
    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
        print("✅ fastembed")
    except ImportError:
        print("❌ fastembed - run: pip install -r requirements.txt")
        all_checks_passed = False
    
    try:
        import chromadb
        print("✅ chromadb")
    except ImportError:
        print("❌ chromadb - run: pip install -r requirements.txt")
        all_checks_passed = False
    
    try:
        from rank_bm25 import BM25Okapi
        print("✅ rank-bm25")
    except ImportError:
        print("⚠️  rank-bm25 (optional for sparse retrieval)")
    
    # Check 5: Indexes
    print("\n🗂️  Index Check")
    indexes_exist = True
    if Path("chroma_db").exists():
        print("✅ Dense index (ChromaDB) exists")
    else:
        print("❌ Dense index not found")
        indexes_exist = False
    
    if Path("data/processed/chunks.json").exists():
        print("✅ Chunks file exists")
    else:
        print("❌ Chunks file not found")
        indexes_exist = False
    
    if Path("data/processed/bm25_index.pkl").exists():
        print("✅ Sparse index (BM25) exists")
    else:
        print("⚠️  Sparse index not found (will run without BM25)")
    
    # Summary
    print_header("Setup Summary")
    
    if all_checks_passed and indexes_exist:
        print("🎉 All checks passed! You're ready to go!")
        print("\nRun the application:")
        print("   streamlit run app.py")
    
    elif all_checks_passed and not indexes_exist:
        print("✅ Prerequisites met!")
        print("⚠️  Indexes not built yet")
        print("\nNext steps:")
        print("1. Run ingestion (ONE TIME):")
        print("   python ingest_advanced.py")
        print("\n2. Start the app:")
        print("   streamlit run app.py")
    
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        if not files_ok:
            print("- Ensure nephrology.pdf is in ../data/")
            print("- Copy .env.example to .env and add your API keys")
        if not env_ok:
            print("- Add API keys to .env file")
        print("\n- Install dependencies:")
        print("  pip install -r requirements.txt")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
