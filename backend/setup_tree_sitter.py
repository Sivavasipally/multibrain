#!/usr/bin/env python3
"""
Tree-sitter Language Parser Setup Script

This script sets up Tree-sitter language parsers for the RAG Chatbot PWA system.
It downloads, compiles, and installs language parsers for supported programming
languages to enable syntax-aware code parsing.

Supported Languages:
- Python: Enhanced Python code parsing
- JavaScript/TypeScript: Modern JS/TS syntax support
- Java: Enterprise Java language support
- C/C++: Systems programming language support
- Go: Google Go language support
- Rust: Mozilla Rust language support

Usage:
    python setup_tree_sitter.py [--languages LANG1,LANG2] [--force]

Options:
    --languages: Comma-separated list of languages to install (default: all)
    --force: Force reinstallation even if parsers already exist
    --verbose: Enable verbose logging during installation

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TreeSitterSetup:
    """
    Tree-sitter language parser setup and installation manager
    
    This class handles the automated installation of Tree-sitter language
    parsers by downloading grammar repositories, compiling them, and installing
    the resulting shared libraries for use by the Tree-sitter service.
    """
    
    def __init__(self, lib_dir: Optional[str] = None):
        """
        Initialize Tree-sitter setup manager
        
        Args:
            lib_dir: Custom library directory (default: backend/lib/tree-sitter)
        """
        self.base_dir = Path(__file__).parent
        self.lib_dir = Path(lib_dir) if lib_dir else self.base_dir / 'lib' / 'tree-sitter'
        
        # Ensure library directory exists
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        
        # Language parser configurations
        self.language_configs = {
            'python': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-python.git',
                'lib_name': 'tree-sitter-python',
                'priority': 'high'  # Most commonly used
            },
            'javascript': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-javascript.git', 
                'lib_name': 'tree-sitter-javascript',
                'priority': 'high'
            },
            'typescript': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-typescript.git',
                'lib_name': 'tree-sitter-typescript',
                'priority': 'medium'
            },
            'java': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-java.git',
                'lib_name': 'tree-sitter-java',
                'priority': 'medium'
            },
            'cpp': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-cpp.git',
                'lib_name': 'tree-sitter-cpp',
                'priority': 'medium'
            },
            'go': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-go.git',
                'lib_name': 'tree-sitter-go',
                'priority': 'low'
            },
            'rust': {
                'repo': 'https://github.com/tree-sitter/tree-sitter-rust.git',
                'lib_name': 'tree-sitter-rust',
                'priority': 'low'
            }
        }
        
        logger.info(f"Tree-sitter setup initialized with library directory: {self.lib_dir}")
    
    def check_dependencies(self) -> bool:
        """
        Check if required dependencies are available
        
        Verifies that git, make, and C compiler are available for building
        Tree-sitter language parsers.
        
        Returns:
            bool: True if all dependencies are available
        """
        logger.info("Checking system dependencies...")
        
        required_commands = ['git', 'make', 'gcc']
        missing_commands = []
        
        for cmd in required_commands:
            try:
                result = subprocess.run(['which', cmd], capture_output=True, text=True)
                if result.returncode != 0:
                    missing_commands.append(cmd)
                else:
                    logger.debug(f"Found {cmd}: {result.stdout.strip()}")
            except Exception as e:
                logger.warning(f"Could not check for {cmd}: {e}")
                missing_commands.append(cmd)
        
        if missing_commands:
            logger.error(f"Missing required dependencies: {', '.join(missing_commands)}")
            logger.error("Please install the missing dependencies:")
            logger.error("  Ubuntu/Debian: sudo apt install git build-essential")
            logger.error("  CentOS/RHEL: sudo yum install git gcc make")
            logger.error("  macOS: xcode-select --install")
            return False
        
        logger.info("All required dependencies are available")
        return True
    
    def install_language_parsers(self, languages: Optional[List[str]] = None, 
                               force: bool = False) -> Dict[str, bool]:
        """
        Install Tree-sitter language parsers
        
        Downloads and compiles Tree-sitter language grammars for the specified
        languages, creating shared libraries that can be used by the Tree-sitter
        service for syntax-aware code parsing.
        
        Args:
            languages: List of languages to install (default: all supported)
            force: Force reinstallation even if libraries exist
            
        Returns:
            Dict[str, bool]: Installation results for each language
        """
        if languages is None:
            languages = list(self.language_configs.keys())
        
        logger.info(f"Installing Tree-sitter parsers for: {', '.join(languages)}")
        
        if not self.check_dependencies():
            logger.error("Cannot proceed without required dependencies")
            return {lang: False for lang in languages}
        
        results = {}
        
        for language in languages:
            if language not in self.language_configs:
                logger.warning(f"Unsupported language: {language}")
                results[language] = False
                continue
            
            try:
                success = self._install_single_parser(language, force)
                results[language] = success
                
                if success:
                    logger.info(f"✓ Successfully installed {language} parser")
                else:
                    logger.error(f"✗ Failed to install {language} parser")
                    
            except Exception as e:
                logger.error(f"✗ Error installing {language} parser: {e}")
                results[language] = False
        
        # Summary
        successful = sum(1 for result in results.values() if result)
        total = len(results)
        logger.info(f"Installation complete: {successful}/{total} parsers installed successfully")
        
        return results
    
    def _install_single_parser(self, language: str, force: bool) -> bool:
        """
        Install a single Tree-sitter language parser
        
        Args:
            language: Language name to install
            force: Force reinstallation
            
        Returns:
            bool: True if installation succeeded
        """
        config = self.language_configs[language]
        lib_name = config['lib_name']
        lib_file = self.lib_dir / f"{lib_name}.so"
        
        # Check if already installed
        if lib_file.exists() and not force:
            logger.info(f"Parser for {language} already exists, skipping")
            return True
        
        logger.info(f"Installing {language} parser from {config['repo']}")
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Clone the repository
                logger.debug(f"Cloning {language} grammar repository...")
                result = subprocess.run([
                    'git', 'clone', '--depth', '1', config['repo'], str(temp_path / language)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.error(f"Failed to clone {language} repository: {result.stderr}")
                    return False
                
                repo_path = temp_path / language
                
                # Build the parser
                logger.debug(f"Building {language} parser...")
                
                # Check for different build systems
                if (repo_path / 'Makefile').exists():
                    # Use Makefile if available
                    result = subprocess.run(['make'], cwd=repo_path, capture_output=True, text=True)
                elif (repo_path / 'src').exists():
                    # Manual compilation for parsers without Makefile
                    result = self._compile_manually(repo_path, lib_name)
                else:
                    logger.error(f"No build system found for {language}")
                    return False
                
                if result.returncode != 0:
                    logger.error(f"Failed to build {language} parser: {result.stderr}")
                    return False
                
                # Find and copy the compiled library
                lib_sources = list(repo_path.glob('**/*.so')) or list(repo_path.glob('**/*.dylib'))
                
                if not lib_sources:
                    logger.error(f"No compiled library found for {language}")
                    return False
                
                # Copy the library to our lib directory
                shutil.copy2(lib_sources[0], lib_file)
                logger.debug(f"Installed {language} parser to {lib_file}")
                
                return True
                
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout during {language} parser installation")
                return False
            except Exception as e:
                logger.error(f"Unexpected error installing {language} parser: {e}")
                return False
    
    def _compile_manually(self, repo_path: Path, lib_name: str) -> subprocess.CompletedProcess:
        """
        Manually compile a Tree-sitter parser
        
        Used when no Makefile is available. Compiles the parser.c and scanner.c
        files found in the src/ directory.
        
        Args:
            repo_path: Path to the cloned repository
            lib_name: Name for the compiled library
            
        Returns:
            subprocess.CompletedProcess: Compilation result
        """
        src_path = repo_path / 'src'
        
        # Find source files
        parser_c = src_path / 'parser.c'
        scanner_files = list(src_path.glob('scanner.*'))
        
        # Build compilation command
        compile_cmd = [
            'gcc',
            '-shared',
            '-fPIC',
            '-O3',
            '-I', str(src_path),
            str(parser_c)
        ]
        
        # Add scanner files if they exist
        for scanner in scanner_files:
            if scanner.suffix in ['.c', '.cc', '.cpp']:
                compile_cmd.append(str(scanner))
        
        # Output file
        compile_cmd.extend(['-o', f'{lib_name}.so'])
        
        logger.debug(f"Manual compilation command: {' '.join(compile_cmd)}")
        
        return subprocess.run(compile_cmd, cwd=repo_path, capture_output=True, text=True)
    
    def list_installed_parsers(self) -> List[str]:
        """
        List currently installed Tree-sitter parsers
        
        Returns:
            List[str]: Names of installed parsers
        """
        installed = []
        
        for language, config in self.language_configs.items():
            lib_file = self.lib_dir / f"{config['lib_name']}.so"
            if lib_file.exists():
                installed.append(language)
        
        return installed
    
    def clean_parsers(self) -> bool:
        """
        Remove all installed Tree-sitter parsers
        
        Returns:
            bool: True if cleanup succeeded
        """
        logger.info("Cleaning installed Tree-sitter parsers...")
        
        try:
            if self.lib_dir.exists():
                shutil.rmtree(self.lib_dir)
                self.lib_dir.mkdir(parents=True, exist_ok=True)
                logger.info("All Tree-sitter parsers removed")
                return True
        except Exception as e:
            logger.error(f"Failed to clean parsers: {e}")
            return False

def main():
    """Main entry point for the Tree-sitter setup script"""
    parser = argparse.ArgumentParser(description='Setup Tree-sitter language parsers')
    parser.add_argument('--languages', type=str, 
                       help='Comma-separated list of languages to install')
    parser.add_argument('--force', action='store_true',
                       help='Force reinstallation of existing parsers')
    parser.add_argument('--clean', action='store_true',
                       help='Remove all installed parsers')
    parser.add_argument('--list', action='store_true',
                       help='List installed parsers')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize setup manager
    setup = TreeSitterSetup()
    
    if args.list:
        installed = setup.list_installed_parsers()
        if installed:
            print("Installed Tree-sitter parsers:")
            for lang in installed:
                print(f"  - {lang}")
        else:
            print("No Tree-sitter parsers installed")
        return
    
    if args.clean:
        success = setup.clean_parsers()
        sys.exit(0 if success else 1)
    
    # Parse language list
    languages = None
    if args.languages:
        languages = [lang.strip() for lang in args.languages.split(',')]
    
    # Install parsers
    results = setup.install_language_parsers(languages, args.force)
    
    # Exit with appropriate code
    failed_count = sum(1 for success in results.values() if not success)
    sys.exit(failed_count)

if __name__ == '__main__':
    main()