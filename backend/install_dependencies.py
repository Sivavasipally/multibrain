#!/usr/bin/env python3
"""
Dependency installation script for Python 3.13 compatibility
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def install_core_dependencies():
    """Install core Flask and basic dependencies"""
    core_packages = [
        "Flask>=3.0.0",
        "Flask-SQLAlchemy>=3.1.1", 
        "Flask-CORS>=4.0.0",
        "Flask-JWT-Extended>=4.6.0",
        "SQLAlchemy>=2.0.25",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "werkzeug>=3.0.0",
        "click>=8.1.0",
        "itsdangerous>=2.1.0",
        "jinja2>=3.1.0",
        "markupsafe>=2.1.0"
    ]
    
    for package in core_packages:
        if not run_command(f"uv pip install {package}", f"Installing {package}"):
            print(f"⚠️  Warning: Failed to install {package}")


def install_optional_dependencies():
    """Install optional dependencies with fallbacks"""
    optional_packages = [
        ("numpy>=1.24.4", "NumPy for numerical operations"),
        ("pandas>=2.1.4", "Pandas for data processing"),
        ("python-docx>=1.1.0", "Python-docx for Word document processing"),
        ("openpyxl>=3.1.2", "OpenPyXL for Excel file processing"),
        ("psutil>=5.9.0", "PSUtil for system monitoring"),
        ("google-generativeai>=0.3.2", "Google Generative AI"),
        ("openai>=1.6.1", "OpenAI API client"),
        ("gunicorn>=21.2.0", "Gunicorn WSGI server"),
        ("pytest>=7.4.3", "PyTest for testing"),
        ("black>=23.11.0", "Black code formatter"),
        ("flake8>=6.1.0", "Flake8 linter")
    ]
    
    for package, description in optional_packages:
        run_command(f"uv pip install {package}", f"Installing {description}")


def install_ai_dependencies():
    """Install AI/ML dependencies with special handling"""
    print(f"\n{'='*60}")
    print("🤖 Installing AI/ML Dependencies")
    print(f"{'='*60}")
    
    # Try to install sentence-transformers
    if run_command("uv pip install sentence-transformers>=2.2.2", "Installing Sentence Transformers"):
        print("✅ Sentence Transformers installed successfully")
    else:
        print("⚠️  Warning: Sentence Transformers installation failed")
        print("💡 You may need to install PyTorch manually first:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    
    # Try to install FAISS
    if run_command("uv pip install faiss-cpu>=1.7.4", "Installing FAISS CPU"):
        print("✅ FAISS CPU installed successfully")
    else:
        print("⚠️  Warning: FAISS CPU installation failed")
        print("💡 Alternative installation methods:")
        print("   conda install -c conda-forge faiss-cpu")
        print("   or use a different vector database")


def install_document_processing():
    """Install document processing dependencies"""
    print(f"\n{'='*60}")
    print("📄 Installing Document Processing Dependencies")
    print(f"{'='*60}")
    
    # Try PyMuPDF (fitz)
    if run_command("uv pip install PyMuPDF>=1.23.8", "Installing PyMuPDF for PDF processing"):
        print("✅ PyMuPDF installed successfully")
    else:
        print("⚠️  Warning: PyMuPDF installation failed")
        print("💡 Alternative: Use PyPDF2 instead")
        run_command("uv pip install PyPDF2>=3.0.1", "Installing PyPDF2 as fallback")


def create_minimal_requirements():
    """Create a minimal requirements file that works"""
    minimal_requirements = """# Minimal requirements for Python 3.13
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.1
Flask-CORS>=4.0.0
Flask-JWT-Extended>=4.6.0
SQLAlchemy>=2.0.25
python-dotenv>=1.0.0
requests>=2.31.0
werkzeug>=3.0.0
click>=8.1.0
itsdangerous>=2.1.0
jinja2>=3.1.0
markupsafe>=2.1.0
numpy>=1.24.4
pandas>=2.1.4
python-docx>=1.1.0
openpyxl>=3.1.2
psutil>=5.9.0
google-generativeai>=0.3.2
openai>=1.6.1
gunicorn>=21.2.0
pytest>=7.4.3
black>=23.11.0
flake8>=6.1.0
"""
    
    with open("requirements-minimal.txt", "w") as f:
        f.write(minimal_requirements)
    
    print("📝 Created requirements-minimal.txt")


def main():
    """Main installation process"""
    print("🚀 RAG Chatbot Dependency Installation")
    print("=" * 60)
    print("This script will install dependencies compatible with Python 3.13")
    print("Some packages may fail - that's normal, we'll provide alternatives")
    
    # Check Python version
    python_version = sys.version_info
    print(f"\n🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 8:
        print("❌ Error: Python 3.8+ required")
        sys.exit(1)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("👋 Exiting. Please activate your virtual environment first.")
            sys.exit(1)
    
    # Install dependencies in stages
    print("\n🔧 Stage 1: Core Dependencies")
    install_core_dependencies()
    
    print("\n🔧 Stage 2: Optional Dependencies")
    install_optional_dependencies()
    
    print("\n🔧 Stage 3: AI/ML Dependencies")
    install_ai_dependencies()
    
    print("\n🔧 Stage 4: Document Processing")
    install_document_processing()
    
    print("\n🔧 Stage 5: Creating minimal requirements file")
    create_minimal_requirements()
    
    print(f"\n{'='*60}")
    print("🎉 Installation Complete!")
    print(f"{'='*60}")
    print("\n📋 Next Steps:")
    print("1. Check for any failed packages above")
    print("2. Install missing packages manually if needed")
    print("3. Run: python app_local.py to test the application")
    print("\n💡 If you encounter issues:")
    print("- Use requirements-minimal.txt for basic functionality")
    print("- Install AI packages separately with conda if needed")
    print("- Check the documentation for alternative packages")
    
    print("\n🔍 Testing basic imports...")
    test_imports = [
        ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("requests", "Requests")
    ]
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} import successful")
        except ImportError:
            print(f"❌ {name} import failed")


if __name__ == "__main__":
    main()
