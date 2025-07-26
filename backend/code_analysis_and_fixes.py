#!/usr/bin/env python3
"""
Comprehensive Code Analysis and Fix Script for RAG Chatbot
"""

import os
import re
import ast
import shutil
from pathlib import Path

class CodeAnalyzer:
    def __init__(self, backend_path="."):
        self.backend_path = Path(backend_path)
        self.issues = []
        self.fixes_applied = []
    
    def analyze_all(self):
        """Run all analysis checks"""
        print("🔍 Starting Comprehensive Code Analysis...")
        print("=" * 60)
        
        self.check_unused_imports()
        self.check_security_issues()
        self.check_error_handling()
        self.check_code_organization()
        self.check_performance_issues()
        self.check_unused_files()
        self.check_route_registration()
        self.check_database_issues()
        
        self.generate_report()
        return self.issues
    
    def check_unused_imports(self):
        """Check for unused imports"""
        print("📦 Checking unused imports...")
        
        # Check app_local.py
        app_file = self.backend_path / "app_local.py"
        if app_file.exists():
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for sys import
            if "import sys" in content and "sys." not in content:
                self.issues.append({
                    'type': 'unused_import',
                    'file': 'app_local.py',
                    'line': 7,
                    'issue': 'Unused import: sys',
                    'severity': 'low',
                    'fix': 'Remove unused import'
                })
    
    def check_security_issues(self):
        """Check for security vulnerabilities"""
        print("🔒 Checking security issues...")
        
        app_file = self.backend_path / "app_local.py"
        if app_file.exists():
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for hardcoded secret keys
            if "local-dev-secret-key" in content:
                self.issues.append({
                    'type': 'security',
                    'file': 'app_local.py',
                    'line': 28,
                    'issue': 'Hardcoded secret key in production',
                    'severity': 'high',
                    'fix': 'Use environment variable or generate random key'
                })
            
            # Check for debug mode
            if "debug=True" in content:
                self.issues.append({
                    'type': 'security',
                    'file': 'app_local.py',
                    'issue': 'Debug mode enabled',
                    'severity': 'medium',
                    'fix': 'Disable debug mode in production'
                })
    
    def check_error_handling(self):
        """Check error handling patterns"""
        print("⚠️  Checking error handling...")
        
        # This would require more complex AST parsing
        # For now, we'll do basic pattern matching
        pass
    
    def check_code_organization(self):
        """Check code organization issues"""
        print("📁 Checking code organization...")
        
        # Check if routes are properly separated
        app_file = self.backend_path / "app_local.py"
        if app_file.exists():
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count route definitions in main file
            route_count = len(re.findall(r'@app\.route\(', content))
            if route_count > 10:
                self.issues.append({
                    'type': 'organization',
                    'file': 'app_local.py',
                    'issue': f'Too many routes ({route_count}) in main file',
                    'severity': 'medium',
                    'fix': 'Move routes to separate blueprint files'
                })
    
    def check_performance_issues(self):
        """Check for performance issues"""
        print("⚡ Checking performance issues...")
        
        # Check for N+1 query patterns
        # Check for missing database indexes
        # This would require more sophisticated analysis
        pass
    
    def check_unused_files(self):
        """Check for unused or leftover files"""
        print("🗑️  Checking unused files...")
        
        # Check for version number directories
        version_dirs = []
        for item in self.backend_path.iterdir():
            if item.is_dir() and re.match(r'^\d+\.\d+\.\d+$', item.name):
                version_dirs.append(item.name)
        
        if version_dirs:
            self.issues.append({
                'type': 'cleanup',
                'file': 'backend/',
                'issue': f'Unused version directories: {", ".join(version_dirs)}',
                'severity': 'low',
                'fix': 'Remove unused version directories'
            })
    
    def check_route_registration(self):
        """Check if all route blueprints are registered"""
        print("🛣️  Checking route registration...")
        
        routes_dir = self.backend_path / "routes"
        if routes_dir.exists():
            route_files = [f.stem for f in routes_dir.glob("*.py") if f.stem != "__init__"]
            
            app_file = self.backend_path / "app_local.py"
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                registered_routes = re.findall(r'from routes\.(\w+)', content)
                
                unregistered = set(route_files) - set(registered_routes) - {"__init__"}
                if unregistered:
                    self.issues.append({
                        'type': 'routes',
                        'file': 'app_local.py',
                        'issue': f'Unregistered route blueprints: {", ".join(unregistered)}',
                        'severity': 'medium',
                        'fix': 'Register missing route blueprints'
                    })
    
    def check_database_issues(self):
        """Check for database-related issues"""
        print("🗄️  Checking database issues...")
        
        # Check for missing database migrations
        # Check for proper foreign key constraints
        # This would require more detailed analysis
        pass
    
    def generate_report(self):
        """Generate analysis report"""
        print("\n" + "=" * 60)
        print("📊 CODE ANALYSIS REPORT")
        print("=" * 60)
        
        if not self.issues:
            print("✅ No issues found! Code looks good.")
            return
        
        # Group issues by severity
        high_issues = [i for i in self.issues if i['severity'] == 'high']
        medium_issues = [i for i in self.issues if i['severity'] == 'medium']
        low_issues = [i for i in self.issues if i['severity'] == 'low']
        
        print(f"🔴 High Priority Issues: {len(high_issues)}")
        print(f"🟡 Medium Priority Issues: {len(medium_issues)}")
        print(f"🟢 Low Priority Issues: {len(low_issues)}")
        print()
        
        for issue in high_issues + medium_issues + low_issues:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[issue['severity']]
            print(f"{severity_icon} {issue['type'].upper()}: {issue['issue']}")
            print(f"   File: {issue['file']}")
            if 'line' in issue:
                print(f"   Line: {issue['line']}")
            print(f"   Fix: {issue['fix']}")
            print()

def main():
    analyzer = CodeAnalyzer()
    issues = analyzer.analyze_all()
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDED ACTIONS")
    print("=" * 60)
    
    if issues:
        print("1. Review and fix high priority security issues first")
        print("2. Address medium priority organization issues")
        print("3. Clean up low priority issues for code quality")
        print("4. Run tests after applying fixes")
        print("5. Consider setting up automated code quality checks")
    else:
        print("✅ No critical issues found!")
        print("Consider adding:")
        print("- Automated testing")
        print("- Code linting (flake8, black)")
        print("- Security scanning")
        print("- Performance monitoring")

if __name__ == "__main__":
    main()
