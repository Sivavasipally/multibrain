#!/usr/bin/env python3
"""
Dependency installation script using regular pip for Python 3.13 compatibility
"""

import subprocess
import sys
import os


def run_pip_install(package, description=""):
    """Install package using pip"""
    print(f"\n📦 Installing {description or package}...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              check=True, capture_output=True, text=True)
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    """Main installation process"""
    print("🚀 RAG Chatbot Dependency Installation (using pip)")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Core packages that should work with most Python versions
    core_packages = [
        ("Flask>=3.0.0", "Flask web framework"),
        ("Flask-SQLAlchemy>=3.1.1", "Flask SQLAlchemy extension"),
        ("Flask-CORS>=4.0.0", "Flask CORS extension"),
        ("Flask-JWT-Extended>=4.6.0", "Flask JWT extension"),
        ("SQLAlchemy>=2.0.25", "SQLAlchemy ORM"),
        ("python-dotenv>=1.0.0", "Environment variable loader"),
        ("requests>=2.31.0", "HTTP library"),
        ("werkzeug>=3.0.0", "WSGI utility library"),
        ("click>=8.1.0", "Command line interface creation kit"),
        ("itsdangerous>=2.1.0", "Cryptographic signing"),
        ("jinja2>=3.1.0", "Template engine"),
        ("markupsafe>=2.1.0", "Safe string handling")
    ]
    
    print("\n🔧 Installing Core Dependencies...")
    for package, description in core_packages:
        run_pip_install(package, description)
    
    # Data processing packages
    data_packages = [
        ("numpy>=1.24.4", "NumPy for numerical operations"),
        ("pandas>=2.1.4", "Pandas for data processing"),
        ("python-docx>=1.1.0", "Word document processing"),
        ("openpyxl>=3.1.2", "Excel file processing")
    ]
    
    print("\n🔧 Installing Data Processing Dependencies...")
    for package, description in data_packages:
        run_pip_install(package, description)
    
    # AI/ML packages (may fail on some systems)
    ai_packages = [
        ("google-generativeai>=0.3.2", "Google Generative AI"),
        ("openai>=1.6.1", "OpenAI API client")
    ]
    
    print("\n🔧 Installing AI Dependencies...")
    for package, description in ai_packages:
        run_pip_install(package, description)
    
    # Optional packages
    optional_packages = [
        ("psutil>=5.9.0", "System monitoring"),
        ("pytest>=7.4.3", "Testing framework"),
        ("black>=23.11.0", "Code formatter"),
        ("flake8>=6.1.0", "Code linter")
    ]
    
    print("\n🔧 Installing Optional Dependencies...")
    for package, description in optional_packages:
        run_pip_install(package, description)
    
    # Try document processing
    print("\n🔧 Installing Document Processing...")
    if not run_pip_install("PyMuPDF>=1.23.8", "PyMuPDF for PDF processing"):
        print("Trying PyPDF2 as alternative...")
        run_pip_install("PyPDF2>=3.0.1", "PyPDF2 for PDF processing")
    
    # Try AI/ML packages that often fail
    print("\n🔧 Installing Advanced AI Dependencies (may fail)...")
    
    print("Attempting sentence-transformers...")
    if not run_pip_install("sentence-transformers>=2.2.2", "Sentence Transformers"):
        print("💡 Sentence Transformers failed. You may need to install PyTorch first:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    
    print("Attempting faiss-cpu...")
    if not run_pip_install("faiss-cpu>=1.7.4", "FAISS CPU"):
        print("💡 FAISS failed. Alternative installation:")
        print("   conda install -c conda-forge faiss-cpu")
    
    # Test imports
    print("\n🔍 Testing imports...")
    test_imports = [
        ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"),
        ("requests", "Requests"),
        ("dotenv", "python-dotenv"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("docx", "python-docx"),
        ("openpyxl", "OpenPyXL"),
        ("google.generativeai", "Google AI"),
        ("openai", "OpenAI")
    ]
    
    working_imports = []
    failed_imports = []
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name}")
            working_imports.append(name)
        except ImportError:
            print(f"❌ {name}")
            failed_imports.append(name)
    
    print(f"\n📊 Summary:")
    print(f"✅ Working: {len(working_imports)} packages")
    print(f"❌ Failed: {len(failed_imports)} packages")
    
    if failed_imports:
        print(f"\n⚠️  Failed packages: {', '.join(failed_imports)}")
        print("💡 You can still run the application with basic functionality")
    
    print(f"\n🎉 Installation complete!")
    print("📋 Next steps:")
    print("1. Activate your virtual environment if not already active")
    print("2. Run: python app_local.py")
    print("3. Open http://localhost:5000 in your browser")


if __name__ == "__main__":
    main()
