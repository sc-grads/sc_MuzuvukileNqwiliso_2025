#!/usr/bin/env python3
"""
Requirements Check - Check if all required packages are installed.
"""

import sys
import importlib

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False

def main():
    """Check all required packages"""
    print("🔍 Checking Required Packages")
    print("=" * 40)
    
    # Basic requirements
    basic_packages = [
        ('python-dotenv', 'dotenv'),
        ('requests', 'requests'),
        ('pyodbc', 'pyodbc'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('flask', 'flask'),
        ('flask-cors', 'flask_cors'),
    ]
    
    print("\n📦 Basic Packages:")
    basic_ok = True
    for package, import_name in basic_packages:
        if not check_package(package, import_name):
            basic_ok = False
    
    # RAG-specific requirements
    rag_packages = [
        ('sentence-transformers', 'sentence_transformers'),
        ('faiss-cpu', 'faiss'),
        ('psutil', 'psutil'),
    ]
    
    print("\n🤖 RAG Packages:")
    rag_ok = True
    for package, import_name in rag_packages:
        if not check_package(package, import_name):
            rag_ok = False
    
    # Optional packages
    optional_packages = [
        ('scikit-learn', 'sklearn'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
    ]
    
    print("\n🔧 Optional Packages:")
    for package, import_name in optional_packages:
        check_package(package, import_name)
    
    # Summary and installation commands
    print("\n📊 Summary:")
    print("=" * 40)
    
    if basic_ok:
        print("✅ Basic packages are installed")
    else:
        print("❌ Some basic packages are missing")
        print("\n💡 Install missing basic packages:")
        print("pip install python-dotenv requests pyodbc numpy pandas flask flask-cors")
    
    if rag_ok:
        print("✅ RAG packages are installed")
    else:
        print("❌ Some RAG packages are missing")
        print("\n💡 Install missing RAG packages:")
        print("pip install sentence-transformers faiss-cpu psutil")
    
    print(f"\n🐍 Python version: {sys.version}")
    
    if basic_ok and rag_ok:
        print("\n🎉 All required packages are installed!")
        print("   You can run both traditional and RAG agents.")
    elif basic_ok:
        print("\n⚠️  Basic packages installed, RAG packages missing.")
        print("   You can run the traditional agent with: python main_simple.py")
    else:
        print("\n❌ Missing required packages. Please install them first.")

if __name__ == "__main__":
    main()