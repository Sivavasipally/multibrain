"""
Repository service for GitHub/Bitbucket integration
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
try:
    import git
    from git import Repo
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("GitPython not available. Repository cloning will use subprocess.")

class RepositoryService:
    """Service for interacting with Git repositories"""
    
    def __init__(self):
        self.github_api_base = "https://api.github.com"
        self.bitbucket_api_base = "https://api.bitbucket.org/2.0"
        self.base_clone_dir = os.path.join(tempfile.gettempdir(), 'rag_repos')
        os.makedirs(self.base_clone_dir, exist_ok=True)
    
    def parse_repo_url(self, url: str) -> Dict[str, str]:
        """Parse repository URL to extract owner and repo name"""
        parsed = urlparse(url)
        
        if 'github.com' in parsed.netloc:
            provider = 'github'
        elif 'bitbucket.org' in parsed.netloc:
            provider = 'bitbucket'
        else:
            raise ValueError("Unsupported repository provider")
        
        # Extract owner and repo from path
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("Invalid repository URL format")
        
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        
        return {
            'provider': provider,
            'owner': owner,
            'repo': repo
        }
    
    def get_repository_info(self, url: str, access_token: str) -> Dict[str, Any]:
        """Get repository information"""
        repo_info = self.parse_repo_url(url)
        
        if repo_info['provider'] == 'github':
            return self._get_github_repo_info(repo_info['owner'], repo_info['repo'], access_token)
        elif repo_info['provider'] == 'bitbucket':
            return self._get_bitbucket_repo_info(repo_info['owner'], repo_info['repo'], access_token)
    
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
        """Clean up cloned repository with Windows compatibility"""
        try:
            if os.path.exists(clone_path):
                # On Windows, we need to handle read-only files in .git directory
                if os.name == 'nt':  # Windows
                    import stat
                    def handle_remove_readonly(func, path, exc):
                        if os.path.exists(path):
                            os.chmod(path, stat.S_IWRITE)
                            func(path)

                    shutil.rmtree(clone_path, onerror=handle_remove_readonly)
                else:
                    shutil.rmtree(clone_path)
                print(f"Cleaned up repository: {clone_path}")
        except Exception as e:
            print(f"Error cleaning up repository: {e}")
            # Try alternative cleanup method
            try:
                import subprocess
                if os.name == 'nt':  # Windows
                    subprocess.run(['rmdir', '/s', '/q', clone_path], shell=True, check=False)
                else:
                    subprocess.run(['rm', '-rf', clone_path], check=False)
                print(f"Alternative cleanup successful: {clone_path}")
            except Exception as e2:
                print(f"Alternative cleanup also failed: {e2}")
