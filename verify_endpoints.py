#!/usr/bin/env python3
"""
Endpoint Verification Script for RAG Chatbot PWA

This script verifies that all frontend API calls have corresponding backend endpoints
and identifies any mismatches or missing implementations.

Usage:
    python verify_endpoints.py

Author: RAG Chatbot Development Team
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

class EndpointVerifier:
    def __init__(self):
        self.backend_routes = set()
        self.frontend_calls = set()
        self.missing_endpoints = set()
        self.unused_endpoints = set()
        
    def extract_backend_routes(self) -> Set[str]:
        """Extract all route definitions from backend files"""
        routes = set()
        
        # Pattern to match Flask route decorators
        route_pattern = r"@\w+\.route\(['\"]([^'\"]+)['\"].*methods=\[([^\]]+)\]"
        
        backend_dir = Path("backend")
        if not backend_dir.exists():
            print("❌ Backend directory not found")
            return routes
            
        # Search in routes directory
        routes_dir = backend_dir / "routes"
        if routes_dir.exists():
            for py_file in routes_dir.glob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    matches = re.findall(route_pattern, content)
                    
                    for path, methods in matches:
                        # Clean up methods string
                        methods_clean = methods.replace("'", "").replace('"', "").replace(" ", "")
                        method_list = methods_clean.split(",")
                        
                        for method in method_list:
                            if method.strip():
                                # Add /api prefix if not present
                                if not path.startswith('/api'):
                                    full_path = f"/api{path}"
                                else:
                                    full_path = path
                                    
                                route_key = f"{method.strip().upper()} {full_path}"
                                routes.add(route_key)
                                
                except Exception as e:
                    print(f"⚠️  Error reading {py_file}: {e}")
        
        # Also check main app files
        for app_file in ["app.py", "app_local.py"]:
            app_path = backend_dir / app_file
            if app_path.exists():
                try:
                    content = app_path.read_text(encoding='utf-8')
                    matches = re.findall(route_pattern, content)
                    
                    for path, methods in matches:
                        methods_clean = methods.replace("'", "").replace('"', "").replace(" ", "")
                        method_list = methods_clean.split(",")
                        
                        for method in method_list:
                            if method.strip():
                                route_key = f"{method.strip().upper()} {path}"
                                routes.add(route_key)
                                
                except Exception as e:
                    print(f"⚠️  Error reading {app_path}: {e}")
        
        return routes
    
    def extract_frontend_calls(self) -> Set[str]:
        """Extract all API calls from frontend files"""
        calls = set()
        
        # Patterns to match API calls
        api_patterns = [
            r"api\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
            r"await\s+api\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
            r"response\s*=\s*await\s+api\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"
        ]
        
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return calls
            
        # Search in src directory
        src_dir = frontend_dir / "src"
        if src_dir.exists():
            for ts_file in src_dir.rglob("*.ts*"):
                try:
                    content = ts_file.read_text(encoding='utf-8')
                    
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content)
                        
                        for match in matches:
                            if len(match) == 2:
                                method, path = match
                                # Add /api prefix if not present
                                if not path.startswith('/api'):
                                    full_path = f"/api{path}"
                                else:
                                    full_path = path
                                    
                                call_key = f"{method.upper()} {full_path}"
                                calls.add(call_key)
                                
                except Exception as e:
                    print(f"⚠️  Error reading {ts_file}: {e}")
        
        return calls
    
    def find_missing_endpoints(self) -> Set[str]:
        """Find frontend calls that don't have backend endpoints"""
        return self.frontend_calls - self.backend_routes
    
    def find_unused_endpoints(self) -> Set[str]:
        """Find backend endpoints that aren't called by frontend"""
        return self.backend_routes - self.frontend_calls
    
    def verify_endpoints(self) -> Dict:
        """Main verification function"""
        print("🔍 Extracting backend routes...")
        self.backend_routes = self.extract_backend_routes()
        
        print("🔍 Extracting frontend API calls...")
        self.frontend_calls = self.extract_frontend_calls()
        
        print("🔍 Analyzing endpoint synchronization...")
        self.missing_endpoints = self.find_missing_endpoints()
        self.unused_endpoints = self.find_unused_endpoints()
        
        return {
            'backend_routes': sorted(list(self.backend_routes)),
            'frontend_calls': sorted(list(self.frontend_calls)),
            'missing_endpoints': sorted(list(self.missing_endpoints)),
            'unused_endpoints': sorted(list(self.unused_endpoints)),
            'total_backend': len(self.backend_routes),
            'total_frontend': len(self.frontend_calls),
            'missing_count': len(self.missing_endpoints),
            'unused_count': len(self.unused_endpoints)
        }
    
    def print_report(self, results: Dict):
        """Print a formatted verification report"""
        print("\n" + "="*80)
        print("📊 ENDPOINT SYNCHRONIZATION REPORT")
        print("="*80)
        
        print(f"\n📈 SUMMARY:")
        print(f"   Backend Routes: {results['total_backend']}")
        print(f"   Frontend Calls: {results['total_frontend']}")
        print(f"   Missing Endpoints: {results['missing_count']}")
        print(f"   Unused Endpoints: {results['unused_count']}")
        
        if results['missing_endpoints']:
            print(f"\n❌ MISSING BACKEND ENDPOINTS ({results['missing_count']}):")
            for endpoint in results['missing_endpoints']:
                print(f"   • {endpoint}")
        else:
            print(f"\n✅ All frontend calls have corresponding backend endpoints!")
        
        if results['unused_endpoints']:
            print(f"\n⚠️  UNUSED BACKEND ENDPOINTS ({results['unused_count']}):")
            for endpoint in results['unused_endpoints']:
                print(f"   • {endpoint}")
        else:
            print(f"\n✅ All backend endpoints are used by frontend!")
        
        print(f"\n📋 ALL BACKEND ROUTES ({results['total_backend']}):")
        for route in results['backend_routes']:
            status = "✅" if route in self.frontend_calls else "⚠️"
            print(f"   {status} {route}")
        
        print(f"\n📋 ALL FRONTEND CALLS ({results['total_frontend']}):")
        for call in results['frontend_calls']:
            status = "✅" if call in self.backend_routes else "❌"
            print(f"   {status} {call}")
        
        # Overall status
        if results['missing_count'] == 0:
            print(f"\n🎉 VERIFICATION PASSED: All endpoints are synchronized!")
        else:
            print(f"\n⚠️  VERIFICATION ISSUES: {results['missing_count']} missing endpoints found")
        
        print("="*80)

def main():
    """Main function"""
    print("🚀 Starting endpoint verification...")
    
    verifier = EndpointVerifier()
    results = verifier.verify_endpoints()
    verifier.print_report(results)
    
    # Save results to JSON file
    output_file = "endpoint_verification_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {output_file}")
    except Exception as e:
        print(f"⚠️  Failed to save results: {e}")
    
    # Exit with error code if there are missing endpoints
    if results['missing_count'] > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()