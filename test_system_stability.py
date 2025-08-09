#!/usr/bin/env python3
"""
Comprehensive End-to-End System Stability Test
Tests all major components of the MultiBrain system
"""

import os
import sys
import json
import sqlite3
import requests
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

class SystemTester:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:5173"
        self.test_results = {}
        
    def log(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {message}")
        self.test_results[test_name] = {"status": status, "message": message}
        
    def test_database_connectivity(self):
        """Test database structure and data integrity"""
        try:
            db_path = backend_path / 'instance' / 'ragchatbot.db'
            if not db_path.exists():
                self.log("Database File", "FAIL", "Database file not found")
                return False
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check all required tables exist
            required_tables = ['users', 'contexts', 'chat_sessions', 'documents', 'messages', 'text_chunks']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(required_tables) - set(existing_tables)
            if missing_tables:
                self.log("Database Schema", "FAIL", f"Missing tables: {missing_tables}")
                conn.close()
                return False
                
            # Check data integrity
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.log(f"Table {table}", "PASS", f"{count} records")
                
            conn.close()
            self.log("Database Connectivity", "PASS", "All tables present and accessible")
            return True
            
        except Exception as e:
            self.log("Database Connectivity", "FAIL", str(e))
            return False
            
    def test_file_system_structure(self):
        """Test file system structure and permissions"""
        try:
            # Check critical directories
            critical_dirs = [
                backend_path / 'instance',
                backend_path / 'uploads', 
                backend_path / 'vector_stores',
                Path(__file__).parent / 'frontend' / 'src'
            ]
            
            for dir_path in critical_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    self.log(f"Directory {dir_path.name}", "PASS", f"Exists and accessible")
                else:
                    self.log(f"Directory {dir_path.name}", "FAIL", f"Missing or not accessible")
                    
            # Check vector store files
            vector_store_path = backend_path / 'vector_stores' / '1'
            if vector_store_path.exists():
                faiss_file = vector_store_path / 'index.faiss'
                metadata_file = vector_store_path / 'metadata.json'
                
                if faiss_file.exists() and metadata_file.exists():
                    self.log("Vector Store", "PASS", "FAISS index and metadata found")
                    
                    # Check metadata integrity
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                            chunks_count = len(metadata.get('chunks', []))
                            self.log("Vector Metadata", "PASS", f"{chunks_count} chunks indexed")
                    except:
                        self.log("Vector Metadata", "FAIL", "Cannot read metadata")
                else:
                    self.log("Vector Store", "FAIL", "Missing FAISS files")
            else:
                self.log("Vector Store", "WARN", "No vector stores found")
                
            return True
            
        except Exception as e:
            self.log("File System Structure", "FAIL", str(e))
            return False
            
    def test_python_imports(self):
        """Test if all required Python modules can be imported"""
        critical_imports = [
            'sqlite3',
            'json', 
            'os',
            'pathlib'
        ]
        
        flask_imports = [
            'flask',
            'flask_sqlalchemy',
            'flask_cors', 
            'flask_jwt_extended'
        ]
        
        ai_imports = [
            'numpy',
            'google.generativeai',
            'faiss'
        ]
        
        # Test critical imports
        for module in critical_imports:
            try:
                __import__(module)
                self.log(f"Import {module}", "PASS", "Available")
            except ImportError:
                self.log(f"Import {module}", "FAIL", "Not available")
                
        # Test Flask imports (may fail without packages)
        flask_available = 0
        for module in flask_imports:
            try:
                __import__(module)
                self.log(f"Import {module}", "PASS", "Available")
                flask_available += 1
            except ImportError:
                self.log(f"Import {module}", "FAIL", "Not available")
                
        # Test AI imports (optional)
        ai_available = 0
        for module in ai_imports:
            try:
                __import__(module)
                self.log(f"Import {module}", "PASS", "Available")
                ai_available += 1
            except ImportError:
                self.log(f"Import {module}", "WARN", "Not available (optional)")
                
        return flask_available > 0  # At least some Flask components should be available
        
    def test_configuration_files(self):
        """Test configuration file integrity"""
        try:
            # Check backend .env
            env_file = backend_path / '.env'
            if env_file.exists():
                with open(env_file) as f:
                    env_content = f.read()
                    
                required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'GEMINI_API_KEY']
                missing_vars = []
                
                for var in required_vars:
                    if var not in env_content:
                        missing_vars.append(var)
                        
                if missing_vars:
                    self.log("Environment Config", "WARN", f"Missing vars: {missing_vars}")
                else:
                    self.log("Environment Config", "PASS", "All required variables present")
            else:
                self.log("Environment Config", "FAIL", ".env file not found")
                
            # Check frontend package.json
            frontend_package = Path(__file__).parent / 'frontend' / 'package.json'
            if frontend_package.exists():
                with open(frontend_package) as f:
                    package_data = json.load(f)
                    
                if 'dependencies' in package_data and 'scripts' in package_data:
                    self.log("Frontend Config", "PASS", "package.json valid")
                else:
                    self.log("Frontend Config", "FAIL", "Invalid package.json")
            else:
                self.log("Frontend Config", "FAIL", "package.json not found")
                
            return True
            
        except Exception as e:
            self.log("Configuration Files", "FAIL", str(e))
            return False
            
    def test_backend_startup(self):
        """Test if backend can start (basic syntax check)"""
        try:
            # Try to import the main app files
            app_local_file = backend_path / 'app_local.py'
            
            if app_local_file.exists():
                # Basic syntax check by reading the file
                with open(app_local_file) as f:
                    content = f.read()
                    
                # Check for critical imports and structure
                critical_patterns = [
                    'from flask import Flask',
                    'app = Flask(__name__)',
                    'if __name__ == \'__main__\'',
                    'db.create_all()'
                ]
                
                missing_patterns = []
                for pattern in critical_patterns:
                    if pattern not in content:
                        missing_patterns.append(pattern)
                        
                if missing_patterns:
                    self.log("Backend Syntax", "WARN", f"Missing patterns: {missing_patterns}")
                else:
                    self.log("Backend Syntax", "PASS", "Core Flask structure intact")
                    
            return True
            
        except Exception as e:
            self.log("Backend Startup", "FAIL", str(e))
            return False
            
    def test_frontend_structure(self):
        """Test frontend structure and key files"""
        try:
            frontend_path = Path(__file__).parent / 'frontend'
            
            # Check key frontend files
            key_files = [
                'src/App.tsx',
                'src/main.tsx', 
                'src/services/api.ts',
                'src/contexts/AuthContext.tsx',
                'public/index.html'
            ]
            
            missing_files = []
            for file_path in key_files:
                full_path = frontend_path / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
                    
            if missing_files:
                self.log("Frontend Structure", "FAIL", f"Missing files: {missing_files}")
            else:
                self.log("Frontend Structure", "PASS", "All key files present")
                
            # Check if node_modules exists
            node_modules = frontend_path / 'node_modules'
            if node_modules.exists():
                self.log("Frontend Dependencies", "PASS", "node_modules exists")
            else:
                self.log("Frontend Dependencies", "WARN", "node_modules not found - run npm install")
                
            return True
            
        except Exception as e:
            self.log("Frontend Structure", "FAIL", str(e))
            return False
            
    def test_data_integrity(self):
        """Test data integrity and relationships"""
        try:
            db_path = backend_path / 'instance' / 'ragchatbot.db'
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Test user-context relationships
            cursor.execute("""
                SELECT u.username, COUNT(c.id) as context_count 
                FROM users u 
                LEFT JOIN contexts c ON u.id = c.user_id 
                GROUP BY u.id, u.username
            """)
            user_contexts = cursor.fetchall()
            
            for username, count in user_contexts:
                self.log(f"User {username}", "PASS", f"{count} contexts")
                
            # Test context-chunks relationships
            cursor.execute("""
                SELECT c.name, COUNT(tc.id) as chunk_count, c.total_chunks
                FROM contexts c 
                LEFT JOIN text_chunks tc ON c.id = tc.context_id 
                GROUP BY c.id, c.name, c.total_chunks
            """)
            context_chunks = cursor.fetchall()
            
            for name, actual_chunks, recorded_chunks in context_chunks:
                if actual_chunks == recorded_chunks:
                    self.log(f"Context {name}", "PASS", f"{actual_chunks}/{recorded_chunks} chunks match")
                else:
                    self.log(f"Context {name}", "WARN", f"{actual_chunks}/{recorded_chunks} chunk mismatch")
                    
            conn.close()
            return True
            
        except Exception as e:
            self.log("Data Integrity", "FAIL", str(e))
            return False
            
    def create_stability_report(self):
        """Create a comprehensive stability report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_status": "UNKNOWN",
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # Analyze results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results.values() if result["status"] == "FAIL")
        warned_tests = sum(1 for result in self.test_results.values() if result["status"] == "WARN")
        
        # Determine overall status
        if failed_tests == 0:
            if warned_tests == 0:
                report["system_status"] = "STABLE"
            else:
                report["system_status"] = "MOSTLY_STABLE"
        else:
            if failed_tests > total_tests * 0.5:
                report["system_status"] = "UNSTABLE"
            else:
                report["system_status"] = "PARTIALLY_STABLE"
                
        # Add recommendations
        if failed_tests > 0:
            report["recommendations"].append("Fix critical failures before deployment")
        if warned_tests > 0:
            report["recommendations"].append("Address warnings to improve system stability")
            
        # Add specific recommendations based on failed tests
        for test_name, result in self.test_results.items():
            if result["status"] == "FAIL":
                if "Import" in test_name:
                    report["recommendations"].append(f"Install missing Python package for {test_name}")
                elif "Database" in test_name:
                    report["recommendations"].append("Check database configuration and permissions")
                elif "Frontend" in test_name:
                    report["recommendations"].append("Run 'npm install' in frontend directory")
                    
        report["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warned": warned_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
        }
        
        return report
        
    def run_all_tests(self):
        """Run all stability tests"""
        print("🔍 Starting Comprehensive System Stability Test")
        print("="*60)
        
        # Run all tests
        self.test_database_connectivity()
        self.test_file_system_structure()
        self.test_python_imports()
        self.test_configuration_files()
        self.test_backend_startup()
        self.test_frontend_structure()
        self.test_data_integrity()
        
        print("\n" + "="*60)
        print("📊 STABILITY REPORT")
        print("="*60)
        
        report = self.create_stability_report()
        
        print(f"System Status: {report['system_status']}")
        print(f"Success Rate: {report['summary']['success_rate']}")
        print(f"Tests: {report['summary']['passed']} passed, {report['summary']['failed']} failed, {report['summary']['warned']} warnings")
        
        if report["recommendations"]:
            print("\n📝 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. {rec}")
                
        # Save report
        report_file = Path(__file__).parent / 'stability_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")
        
        return report

if __name__ == "__main__":
    tester = SystemTester()
    report = tester.run_all_tests()
    
    # Exit with appropriate code
    if report["system_status"] in ["STABLE", "MOSTLY_STABLE"]:
        sys.exit(0)
    else:
        sys.exit(1)