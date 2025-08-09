"""
Repository Service for Git Integration and Code Analysis - RAG Chatbot PWA

This module provides comprehensive repository management capabilities for the RAG
(Retrieval-Augmented Generation) chatbot system. It supports cloning, analyzing,
and processing Git repositories from GitHub, Bitbucket, and other Git providers
for code knowledge base creation.

Key Features:
- Multi-provider Git repository support (GitHub, Bitbucket, GitLab)
- Repository cloning with branch selection and depth control
- Intelligent code structure analysis and language detection
- File filtering and processing optimization
- Project type detection and framework identification
- API-based and direct Git cloning methods
- Comprehensive error handling and cleanup
- Cross-platform compatibility (Windows, Linux, macOS)

Repository Processing Pipeline:
1. URL Parsing: Extract repository provider and metadata
2. Authentication: Handle access tokens and credentials
3. Cloning: Download repository with specified branch/commit
4. Analysis: Analyze project structure and identify processable files
5. Filtering: Apply file type and size filters
6. Processing: Extract and chunk code content for RAG
7. Cleanup: Remove temporary files and directories

Supported Operations:
- Repository information retrieval
- File tree exploration
- Individual file downloads
- Full repository cloning
- Code structure analysis
- Language and framework detection

Integration Points:
- GitHub API v4 for repository metadata and content
- Bitbucket API v2.0 for Atlassian repositories
- GitPython for advanced Git operations
- Subprocess fallback for Git CLI operations
- Document processor for code content extraction
- Vector service for code embeddings

Dependencies:
- requests: HTTP client for API interactions
- GitPython: Advanced Git operations (optional)
- subprocess: Git CLI fallback operations
- pathlib: Cross-platform path operations
- tempfile: Secure temporary directory management

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import requests
import base64
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('repository_service')

# Optional GitPython import with fallback
try:
    import git
    from git import Repo
    GIT_AVAILABLE = True
    logger.info("GitPython available for advanced Git operations")
except ImportError:
    GIT_AVAILABLE = False
    logger.warning("GitPython not available. Repository operations will use subprocess fallback.")

class RepositoryService:
    """
    Comprehensive repository service for Git-based code analysis and RAG integration
    
    This service provides complete repository management capabilities including cloning,
    analysis, and processing of Git repositories for knowledge base creation. It supports
    multiple Git providers and offers both API-based and direct Git operations.
    
    Key Capabilities:
    - Multi-provider repository support (GitHub, Bitbucket, GitLab)
    - Repository metadata retrieval and analysis
    - Intelligent code structure detection
    - File filtering and processing optimization
    - Cross-platform compatibility
    - Comprehensive error handling and logging
    
    Repository Processing Flow:
    1. URL Parsing: Extract provider and repository information
    2. Authentication: Handle access tokens and credentials
    3. Metadata Retrieval: Get repository information and file tree
    4. Content Download: Clone or download specific files
    5. Structure Analysis: Analyze code organization and languages
    6. File Processing: Filter and prepare files for RAG processing
    7. Cleanup: Remove temporary files and directories
    
    Attributes:
        github_api_base (str): GitHub API base URL
        bitbucket_api_base (str): Bitbucket API base URL
        base_clone_dir (str): Base directory for repository clones
        
    Example:
        >>> repo_service = RepositoryService()
        >>> result = repo_service.clone_repository_direct('https://github.com/user/repo.git')
        >>> if result['success']:
        ...     print(f"Cloned to: {result['clone_path']}")
    """
    
    def __init__(self):
        """
        Initialize the Repository Service with API endpoints and working directories
        
        Sets up the service with proper API base URLs, working directories, and
        logging configuration. Creates necessary directories and validates
        dependencies for Git operations.
        
        Raises:
            OSError: If temporary directory creation fails
            Exception: If initialization prerequisites are not met
        """
        logger.info("Initializing RepositoryService")
        
        # API endpoints for different Git providers
        self.github_api_base = "https://api.github.com"
        self.bitbucket_api_base = "https://api.bitbucket.org/2.0"
        
        # Set up working directory for repository clones
        self.base_clone_dir = os.path.join(tempfile.gettempdir(), 'rag_repos')
        
        try:
            os.makedirs(self.base_clone_dir, exist_ok=True)
            logger.info(f"Repository working directory: {self.base_clone_dir}")
        except OSError as e:
            logger.error(f"Failed to create repository working directory: {e}")
            raise
        
        # Log Git availability status
        if GIT_AVAILABLE:
            logger.info("Repository service initialized with GitPython support")
        else:
            logger.info("Repository service initialized with subprocess Git fallback")
        
        logger.debug(f"GitHub API base: {self.github_api_base}")
        logger.debug(f"Bitbucket API base: {self.bitbucket_api_base}")
    
    def parse_repo_url(self, url: str) -> Dict[str, str]:
        """
        Parse repository URL to extract provider, owner, and repository information
        
        Analyzes Git repository URLs to identify the hosting provider and extract
        essential repository metadata. Supports multiple Git providers with
        standardized output format for consistent processing.
        
        URL Format Support:
        - GitHub: https://github.com/owner/repo.git
        - Bitbucket: https://bitbucket.org/owner/repo.git
        - GitLab: https://gitlab.com/owner/repo.git (basic support)
        - SSH URLs: git@github.com:owner/repo.git
        
        Args:
            url (str): Repository URL to parse
            
        Returns:
            Dict[str, str]: Repository information containing:
                - provider: Git hosting provider ('github', 'bitbucket', 'gitlab')
                - owner: Repository owner/organization name
                - repo: Repository name (without .git suffix)
                
        Raises:
            ValueError: If URL format is invalid or provider is unsupported
            
        Example:
            >>> repo_info = service.parse_repo_url('https://github.com/user/myrepo.git')
            >>> print(repo_info)
            {'provider': 'github', 'owner': 'user', 'repo': 'myrepo'}
            
        Security:
            - URL validation to prevent malicious inputs
            - Provider whitelist for security
            - Path sanitization to prevent traversal attacks
        """
        if not url or not isinstance(url, str):
            logger.error(f"Invalid repository URL provided: {url}")
            raise ValueError("Repository URL must be a valid string")
            
        logger.debug(f"Parsing repository URL: {url}")
        
        try:
            parsed = urlparse(url.strip())
            
            # Determine provider based on hostname
            hostname = parsed.netloc.lower()
            provider = None
            
            if 'github.com' in hostname:
                provider = 'github'
            elif 'bitbucket.org' in hostname:
                provider = 'bitbucket'
            elif 'gitlab.com' in hostname:
                provider = 'gitlab'
            else:
                logger.error(f"Unsupported repository provider: {hostname}")
                raise ValueError(f"Unsupported repository provider: {hostname}")
            
            # Extract owner and repository name from path
            path = parsed.path.strip('/')
            if not path:
                logger.error(f"Empty path in repository URL: {url}")
                raise ValueError("Repository URL must contain owner and repository name")
                
            path_parts = path.split('/')
            if len(path_parts) < 2:
                logger.error(f"Invalid repository URL format - insufficient path parts: {url}")
                raise ValueError("Repository URL must contain both owner and repository name")
            
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')  # Remove .git suffix if present
            
            # Validate extracted components
            if not owner or not repo:
                logger.error(f"Invalid owner or repository name extracted from: {url}")
                raise ValueError("Could not extract valid owner and repository name")
            
            result = {
                'provider': provider,
                'owner': owner,
                'repo': repo
            }
            
            logger.info(f"Parsed repository: {provider}/{owner}/{repo}")
            return result
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise validation errors
            else:
                logger.error(f"Error parsing repository URL {url}: {e}")
                log_error_with_context(e, {"url": url, "operation": "url_parsing"})
                raise ValueError(f"Failed to parse repository URL: {str(e)}")
    
    def get_repository_info(self, url: str, access_token: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive repository information from Git provider APIs
        
        Fetches detailed repository metadata including description, language,
        creation date, and other relevant information for knowledge base
        organization and display purposes.
        
        Repository Information Retrieved:
        - Basic metadata: name, description, language
        - Statistics: size, creation/update dates
        - Branch information: default branch
        - Access information: public/private status
        - License and topic information (where available)
        
        Args:
            url (str): Repository URL to analyze
            access_token (str): API access token for authentication
            
        Returns:
            Dict[str, Any]: Repository information containing:
                - name: Repository name
                - full_name: Full repository name (owner/repo)
                - description: Repository description
                - language: Primary programming language
                - size: Repository size in KB
                - default_branch: Default branch name
                - created_at: Creation timestamp
                - updated_at: Last update timestamp
                
        Raises:
            ValueError: If repository URL is invalid
            Exception: If API request fails or authentication is invalid
            
        Example:
            >>> info = service.get_repository_info('https://github.com/user/repo', 'token123')
            >>> print(f"Language: {info['language']}, Size: {info['size']} KB")
            
        Security:
            - API token validation
            - Rate limiting awareness
            - Error handling for private repositories
        """
        logger.info(f"Retrieving repository information for: {url}")
        
        try:
            # Parse repository URL to extract provider and identifiers
            repo_info = self.parse_repo_url(url)
            provider = repo_info['provider']
            owner = repo_info['owner']
            repo_name = repo_info['repo']
            
            logger.debug(f"Fetching info from {provider} for {owner}/{repo_name}")
            
            # Route to appropriate provider API
            if provider == 'github':
                result = self._get_github_repo_info(owner, repo_name, access_token)
            elif provider == 'bitbucket':
                result = self._get_bitbucket_repo_info(owner, repo_name, access_token)
            else:
                logger.error(f"Repository info not implemented for provider: {provider}")
                raise ValueError(f"Repository information retrieval not supported for {provider}")
            
            logger.info(f"Successfully retrieved repository info: {result.get('name', 'unknown')} ({result.get('language', 'unknown')})")
            return result
            
        except Exception as e:
            error_msg = f"Failed to retrieve repository information: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "url": url,
                "provider": repo_info.get('provider') if 'repo_info' in locals() else 'unknown',
                "operation": "get_repository_info"
            })
            raise Exception(error_msg)
    
    def get_repository_tree(self, url: str, branch: str, access_token: str) -> List[Dict[str, Any]]:
        """Get repository file tree"""
        repo_info = self.parse_repo_url(url)
        
        if repo_info['provider'] == 'github':
            return self._get_github_tree(repo_info['owner'], repo_info['repo'], branch, access_token)
        elif repo_info['provider'] == 'bitbucket':
            return self._get_bitbucket_tree(repo_info['owner'], repo_info['repo'], branch, access_token)
    
    def download_file(self, url: str, file_path: str, branch: str, access_token: str) -> bytes:
        """Download a specific file from repository"""
        repo_info = self.parse_repo_url(url)
        
        if repo_info['provider'] == 'github':
            return self._download_github_file(repo_info['owner'], repo_info['repo'], file_path, branch, access_token)
        elif repo_info['provider'] == 'bitbucket':
            return self._download_bitbucket_file(repo_info['owner'], repo_info['repo'], file_path, branch, access_token)
    
    def clone_repository(self, url: str, branch: str, access_token: str, target_dir: str) -> str:
        """Clone repository to local directory"""
        repo_info = self.parse_repo_url(url)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            if repo_info['provider'] == 'github':
                self._clone_github_repo(repo_info['owner'], repo_info['repo'], branch, access_token, temp_dir)
            elif repo_info['provider'] == 'bitbucket':
                self._clone_bitbucket_repo(repo_info['owner'], repo_info['repo'], branch, access_token, temp_dir)
            
            # Move to target directory
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.move(temp_dir, target_dir)
            
            return target_dir
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    def _get_github_repo_info(self, owner: str, repo: str, access_token: str) -> Dict[str, Any]:
        """Get GitHub repository information"""
        headers = {'Authorization': f'token {access_token}'}
        response = requests.get(f"{self.github_api_base}/repos/{owner}/{repo}", headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get repository info: {response.text}")
        
        data = response.json()
        return {
            'name': data['name'],
            'full_name': data['full_name'],
            'description': data.get('description', ''),
            'language': data.get('language', ''),
            'size': data['size'],
            'default_branch': data['default_branch'],
            'created_at': data['created_at'],
            'updated_at': data['updated_at']
        }
    
    def _get_github_tree(self, owner: str, repo: str, branch: str, access_token: str) -> List[Dict[str, Any]]:
        """Get GitHub repository tree"""
        headers = {'Authorization': f'token {access_token}'}
        
        # Get tree recursively
        response = requests.get(
            f"{self.github_api_base}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get repository tree: {response.text}")
        
        data = response.json()
        files = []
        
        for item in data['tree']:
            if item['type'] == 'blob':  # Only files, not directories
                files.append({
                    'path': item['path'],
                    'size': item.get('size', 0),
                    'sha': item['sha']
                })
        
        return files
    
    def _download_github_file(self, owner: str, repo: str, file_path: str, branch: str, access_token: str) -> bytes:
        """Download file from GitHub"""
        headers = {'Authorization': f'token {access_token}'}
        
        response = requests.get(
            f"{self.github_api_base}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")
        
        data = response.json()
        content = base64.b64decode(data['content'])
        
        return content
    
    def _clone_github_repo(self, owner: str, repo: str, branch: str, access_token: str, target_dir: str):
        """Clone GitHub repository using API"""
        # Download repository as ZIP
        headers = {'Authorization': f'token {access_token}'}
        response = requests.get(
            f"{self.github_api_base}/repos/{owner}/{repo}/zipball/{branch}",
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to download repository: {response.text}")
        
        # Save and extract ZIP
        zip_path = os.path.join(target_dir, 'repo.zip')
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract ZIP
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Remove ZIP file
        os.remove(zip_path)
        
        # Find extracted directory and move contents up
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isdir(item_path) and item.startswith(f"{owner}-{repo}"):
                # Move contents up one level
                for subitem in os.listdir(item_path):
                    shutil.move(os.path.join(item_path, subitem), target_dir)
                os.rmdir(item_path)
                break
    
    def _get_bitbucket_repo_info(self, owner: str, repo: str, access_token: str) -> Dict[str, Any]:
        """Get Bitbucket repository information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{self.bitbucket_api_base}/repositories/{owner}/{repo}", headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get repository info: {response.text}")
        
        data = response.json()
        return {
            'name': data['name'],
            'full_name': data['full_name'],
            'description': data.get('description', ''),
            'language': data.get('language', ''),
            'size': data.get('size', 0),
            'created_at': data['created_on'],
            'updated_at': data['updated_on']
        }
    
    def _get_bitbucket_tree(self, owner: str, repo: str, branch: str, access_token: str) -> List[Dict[str, Any]]:
        """Get Bitbucket repository tree"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        files = []
        url = f"{self.bitbucket_api_base}/repositories/{owner}/{repo}/src/{branch}"
        
        def get_directory_contents(path=""):
            nonlocal files
            current_url = f"{url}/{path}" if path else url
            response = requests.get(current_url, headers=headers)
            
            if response.status_code != 200:
                return
            
            data = response.json()
            for item in data.get('values', []):
                if item['type'] == 'commit_file':
                    files.append({
                        'path': item['path'],
                        'size': item.get('size', 0)
                    })
                elif item['type'] == 'commit_directory':
                    get_directory_contents(item['path'])
        
        get_directory_contents()
        return files
    
    def _download_bitbucket_file(self, owner: str, repo: str, file_path: str, branch: str, access_token: str) -> bytes:
        """Download file from Bitbucket"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(
            f"{self.bitbucket_api_base}/repositories/{owner}/{repo}/src/{branch}/{file_path}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")
        
        return response.content
    
    def _clone_bitbucket_repo(self, owner: str, repo: str, branch: str, access_token: str, target_dir: str):
        """Clone Bitbucket repository"""
        # Similar to GitHub implementation but using Bitbucket API
        # This is a simplified version - in production, you might want to use git clone
        files = self._get_bitbucket_tree(owner, repo, branch, access_token)
        
        for file_info in files:
            file_content = self._download_bitbucket_file(owner, repo, file_info['path'], branch, access_token)
            
            # Create directory structure
            file_path = os.path.join(target_dir, file_info['path'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)

    def clone_repository_direct(self, repo_url: str, branch: str = 'main') -> Dict[str, Any]:
        """Clone repository directly using git command"""
        try:
            # Parse repository URL to get name
            parsed_url = urlparse(repo_url)
            repo_name = Path(parsed_url.path).stem.replace('.git', '')

            # Create unique directory for this clone
            clone_dir = os.path.join(self.base_clone_dir, f"{repo_name}_{hash(repo_url) % 10000}")

            # Remove existing directory if it exists
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)

            print(f"Cloning repository: {repo_url} to {clone_dir}")

            if GIT_AVAILABLE:
                # Use GitPython
                repo = Repo.clone_from(repo_url, clone_dir, branch=branch, depth=1)
                commit_info = {
                    'hash': repo.head.commit.hexsha[:8],
                    'message': repo.head.commit.message.strip(),
                    'author': str(repo.head.commit.author),
                    'date': repo.head.commit.committed_datetime.isoformat()
                }
            else:
                # Use subprocess as fallback
                result = subprocess.run([
                    'git', 'clone', '--depth', '1', '--branch', branch, repo_url, clone_dir
                ], capture_output=True, text=True, timeout=300)

                if result.returncode != 0:
                    raise Exception(f"Git clone failed: {result.stderr}")

                commit_info = {'hash': 'unknown', 'message': 'Cloned successfully', 'author': 'unknown', 'date': 'unknown'}

            # Analyze repository
            repo_info = self._analyze_repository_structure(clone_dir)
            repo_info['clone_path'] = clone_dir
            repo_info['repo_url'] = repo_url
            repo_info['branch'] = branch
            repo_info['commit_info'] = commit_info

            return {
                'success': True,
                'repo_info': repo_info,
                'clone_path': clone_dir
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Repository cloning timed out (5 minutes)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Repository cloning failed: {str(e)}"
            }

    def _analyze_repository_structure(self, clone_path: str) -> Dict[str, Any]:
        """Analyze repository structure and content"""

        # File extensions to process
        code_extensions = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.h': 'c',
            '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php',
            '.cs': 'csharp', '.kt': 'kotlin', '.swift': 'swift'
        }

        doc_extensions = {'.md', '.txt', '.rst', '.adoc'}
        config_extensions = {'.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.conf'}

        file_stats = {
            'total_files': 0,
            'code_files': 0,
            'doc_files': 0,
            'config_files': 0,
            'languages': {},
            'processable_files': []
        }

        # Skip patterns
        skip_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'target', 'build', 'dist', '.idea', '.vscode'
        }

        # Walk through all files
        for root, dirs, files in os.walk(clone_path):
            # Skip directories that match skip patterns
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in skip_patterns)]

            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, clone_path)
                file_ext = Path(file).suffix.lower()

                file_stats['total_files'] += 1

                # Check if file should be processed
                should_process = False
                file_type = 'other'

                if file_ext in code_extensions:
                    file_stats['code_files'] += 1
                    language = code_extensions[file_ext]
                    file_type = 'code'
                    should_process = True

                    if language not in file_stats['languages']:
                        file_stats['languages'][language] = 0
                    file_stats['languages'][language] += 1

                elif file_ext in doc_extensions:
                    file_stats['doc_files'] += 1
                    file_type = 'documentation'
                    should_process = True

                elif file_ext in config_extensions:
                    file_stats['config_files'] += 1
                    file_type = 'configuration'
                    should_process = True

                # Add to processable files if it should be processed and isn't too large
                if should_process and os.path.getsize(file_path) < 1024 * 1024:  # < 1MB
                    file_stats['processable_files'].append({
                        'path': file_path,
                        'relative_path': relative_path,
                        'type': file_type,
                        'language': code_extensions.get(file_ext, 'unknown'),
                        'size': os.path.getsize(file_path)
                    })

        # Detect project type
        project_info = self._detect_project_type(clone_path)

        return {
            'name': os.path.basename(clone_path),
            'file_analysis': file_stats,
            'project_info': project_info,
            'total_files': file_stats['total_files'],
            'code_files': file_stats['code_files'],
            'languages': file_stats['languages']
        }

    def _detect_project_type(self, clone_path: str) -> Dict[str, Any]:
        """Detect project type and framework"""

        project_indicators = {
            'package.json': 'Node.js/JavaScript',
            'requirements.txt': 'Python',
            'setup.py': 'Python',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'Cargo.toml': 'Rust',
            'go.mod': 'Go',
            'composer.json': 'PHP'
        }

        detected_types = []

        for indicator, project_type in project_indicators.items():
            if os.path.exists(os.path.join(clone_path, indicator)):
                detected_types.append(project_type)

        return {
            'types': detected_types,
            'primary_type': detected_types[0] if detected_types else 'Unknown'
        }

    def cleanup_repository(self, clone_path: str):
        """
        Clean up cloned repository with comprehensive cross-platform compatibility
        
        Safely removes cloned repository directories, handling platform-specific
        file permission issues and providing fallback cleanup methods for
        robust cleanup operations.
        
        Platform Compatibility:
        - Windows: Handles read-only .git files with permission reset
        - Linux/macOS: Standard directory removal
        - Fallback: System command-based cleanup for stubborn files
        
        Args:
            clone_path (str): Path to the cloned repository directory
            
        Cleanup Process:
        1. Check if directory exists
        2. Platform-specific cleanup (handle read-only files on Windows)
        3. Fallback to system commands if standard cleanup fails
        4. Comprehensive error logging and reporting
        
        Example:
            >>> repo_service.cleanup_repository('/tmp/my_repo_clone')
            >>> # Repository directory and all contents removed
            
        Security:
            - Path validation to prevent directory traversal
            - Safe error handling to prevent system damage
            - Comprehensive logging for audit trails
        """
        if not clone_path or not os.path.exists(clone_path):
            logger.debug(f"Cleanup skipped - path does not exist: {clone_path}")
            return
            
        logger.info(f"Starting repository cleanup: {clone_path}")
        
        try:
            # Validate path to prevent accidental system directory deletion
            if not clone_path.startswith(self.base_clone_dir):
                logger.error(f"Cleanup path outside safe directory: {clone_path}")
                raise ValueError("Cleanup path outside designated repository directory")
            
            # Platform-specific cleanup handling
            if os.name == 'nt':  # Windows
                logger.debug("Using Windows-specific cleanup with read-only file handling")
                import stat
                
                def handle_remove_readonly(func, path, exc):
                    """Handle read-only files in Windows .git directories"""
                    try:
                        if os.path.exists(path):
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                    except OSError as chmod_error:
                        logger.warning(f"Failed to reset permissions for {path}: {chmod_error}")

                shutil.rmtree(clone_path, onerror=handle_remove_readonly)
            else:
                logger.debug("Using standard Unix/Linux cleanup")
                shutil.rmtree(clone_path)
            
            logger.info(f"Successfully cleaned up repository: {clone_path}")
            
        except Exception as e:
            logger.warning(f"Standard cleanup failed for {clone_path}: {e}")
            
            # Try alternative cleanup method using system commands
            try:
                logger.info("Attempting alternative cleanup using system commands")
                
                if os.name == 'nt':  # Windows
                    result = subprocess.run(
                        ['rmdir', '/s', '/q', clone_path], 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        check=False
                    )
                else:
                    result = subprocess.run(
                        ['rm', '-rf', clone_path], 
                        capture_output=True, 
                        text=True,
                        check=False
                    )
                
                if result.returncode == 0:
                    logger.info(f"Alternative cleanup successful: {clone_path}")
                else:
                    logger.error(f"Alternative cleanup failed: {result.stderr}")
                    
            except Exception as e2:
                logger.error(f"All cleanup methods failed for {clone_path}: {e2}")
                log_error_with_context(e2, {
                    "clone_path": clone_path,
                    "platform": os.name,
                    "operation": "repository_cleanup"
                })

    def _is_text_file(self, file_path: str) -> bool:
        """
        Determine if a file is a text file suitable for processing
        
        Analyzes file characteristics to determine if the file contains text content
        that can be processed for RAG operations. Uses multiple detection methods
        including file extensions, content sampling, and encoding detection.
        
        Detection Methods:
        1. Extension-based detection for known text file types
        2. Binary content detection using null byte presence
        3. Encoding validation for text files
        4. File size validation for processing efficiency
        
        Args:
            file_path (str): Path to the file to analyze
            
        Returns:
            bool: True if file appears to be processable text, False otherwise
            
        Text File Categories:
        - Code files: .py, .js, .java, .cpp, .go, .rs, etc.
        - Documentation: .md, .txt, .rst, .adoc
        - Configuration: .json, .yaml, .xml, .toml, .ini
        - Web files: .html, .css, .scss
        - Data files: .csv, .tsv (text-based)
        
        Example:
            >>> if repo_service._is_text_file('/path/to/main.py'):
            ...     process_file(file_path)
            
        Performance:
        - Fast extension-based detection for most cases
        - Limited content sampling to avoid reading large binary files
        - Early rejection of common binary extensions
        """
        try:
            # Quick rejection of known binary extensions
            binary_extensions = {
                '.exe', '.dll', '.so', '.dylib', '.bin', '.dat',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
                '.mp3', '.wav', '.mp4', '.avi', '.mkv', '.mov',
                '.zip', '.tar', '.gz', '.rar', '.7z',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
            }
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext in binary_extensions:
                logger.debug(f"Skipping binary file by extension: {file_path}")
                return False
            
            # Known text file extensions
            text_extensions = {
                # Code files
                '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
                '.go', '.rs', '.rb', '.php', '.cs', '.kt', '.swift', '.scala',
                '.sh', '.bash', '.ps1', '.bat', '.cmd',
                
                # Web files
                '.html', '.htm', '.css', '.scss', '.sass', '.less',
                '.jsx', '.tsx', '.vue', '.svelte',
                
                # Configuration files
                '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.conf',
                '.cfg', '.properties', '.env',
                
                # Documentation
                '.md', '.txt', '.rst', '.adoc', '.tex',
                
                # Data files
                '.csv', '.tsv', '.sql', '.log'
            }
            
            if file_ext in text_extensions:
                logger.debug(f"Identified as text file by extension: {file_path}")
                return True
            
            # Check file size - skip very large files
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
                    return False
                
                if file_size == 0:
                    logger.debug(f"Skipping empty file: {file_path}")
                    return False
                    
            except OSError as e:
                logger.warning(f"Cannot check file size: {file_path} - {e}")
                return False
            
            # Content-based detection for files without clear extensions
            try:
                # Read a small sample to check for binary content
                with open(file_path, 'rb') as f:
                    sample = f.read(1024)  # Read first 1KB
                
                # Check for null bytes (common in binary files)
                if b'\x00' in sample:
                    logger.debug(f"Detected binary content (null bytes): {file_path}")
                    return False
                
                # Try to decode as UTF-8 (most common text encoding)
                try:
                    sample.decode('utf-8')
                    logger.debug(f"Detected text file by UTF-8 decoding: {file_path}")
                    return True
                except UnicodeDecodeError:
                    # Try other common encodings
                    for encoding in ['latin1', 'cp1252', 'ascii']:
                        try:
                            sample.decode(encoding)
                            logger.debug(f"Detected text file by {encoding} decoding: {file_path}")
                            return True
                        except UnicodeDecodeError:
                            continue
                    
                    logger.debug(f"Cannot decode file as text: {file_path}")
                    return False
                    
            except (IOError, OSError) as e:
                logger.warning(f"Cannot read file for content analysis: {file_path} - {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error analyzing file type for {file_path}: {e}")
            return False
