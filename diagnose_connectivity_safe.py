#!/usr/bin/env python3
"""
🛡️ Safe Connectivity Diagnostic Tool
Diagnoses service connectivity issues without modifying existing system.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

class SafeConnectivityDiagnostic:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "diagnostic_mode": "SAFE_READ_ONLY",
            "system_state": "PRESERVED",
            "findings": [],
            "recommendations": [],
            "safety_status": "PROTECTED"
        }
        
    def log_finding(self, category, status, message, details=None):
        """Log diagnostic finding safely."""
        finding = {
            "category": category,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results["findings"].append(finding)
        
        # Print to console
        status_icon = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
        print(f"{status_icon} [{category}] {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def check_python_environment(self):
        """Check Python environment and dependencies."""
        print("\n🐍 Python Environment Diagnostic...")
        
        # Check Python version
        python_version = sys.version
        self.log_finding("Python", "OK", f"Python version: {python_version}")
        
        # Check requirements.txt
        req_file = Path("requirements.txt")
        if req_file.exists():
            self.log_finding("Dependencies", "OK", "requirements.txt found")
            
            # Read requirements
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().splitlines()
                
                missing_packages = []
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        try:
                            __import__(package_name.replace('-', '_'))
                        except ImportError:
                            missing_packages.append(package_name)
                
                if missing_packages:
                    self.log_finding("Dependencies", "ERROR", 
                                   f"Missing packages: {len(missing_packages)}", 
                                   {"missing": missing_packages[:10]})  # Show first 10
                else:
                    self.log_finding("Dependencies", "OK", "All packages available")
                    
            except Exception as e:
                self.log_finding("Dependencies", "ERROR", f"Error reading requirements: {e}")
        else:
            self.log_finding("Dependencies", "WARNING", "requirements.txt not found")
    
    def check_configuration_files(self):
        """Check configuration files safely."""
        print("\n⚙️ Configuration Files Diagnostic...")
        
        config_files = [
            "app/core/config.py",
            "docker-compose.yml", 
            "alembic.ini",
            ".env",
            "Dockerfile"
        ]
        
        for config_file in config_files:
            file_path = Path(config_file)
            if file_path.exists():
                self.log_finding("Config", "OK", f"{config_file} exists")
                
                # Check file size (basic validation)
                file_size = file_path.stat().st_size
                if file_size > 0:
                    self.log_finding("Config", "OK", f"{config_file} has content ({file_size} bytes)")
                else:
                    self.log_finding("Config", "WARNING", f"{config_file} is empty")
            else:
                self.log_finding("Config", "WARNING", f"{config_file} missing")
    
    def check_database_configuration(self):
        """Check database configuration (read-only)."""
        print("\n🗄️ Database Configuration Diagnostic...")
        
        # Check docker-compose for database services
        docker_compose = Path("docker-compose.yml")
        if docker_compose.exists():
            try:
                with open(docker_compose, 'r') as f:
                    content = f.read()
                
                if 'postgres' in content.lower():
                    self.log_finding("Database", "OK", "PostgreSQL service found in docker-compose")
                
                if 'redis' in content.lower():
                    self.log_finding("Database", "OK", "Redis service found in docker-compose")
                
                # Check for ports
                if '5432' in content:
                    self.log_finding("Database", "OK", "PostgreSQL port 5432 configured")
                if '6379' in content:
                    self.log_finding("Database", "OK", "Redis port 6379 configured")
                    
            except Exception as e:
                self.log_finding("Database", "ERROR", f"Error reading docker-compose: {e}")
        
        # Check for migration files
        migrations_dir = Path("alembic/versions")
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("*.py"))
            self.log_finding("Database", "OK", 
                           f"Database migrations found: {len(migration_files)} files")
        else:
            self.log_finding("Database", "WARNING", "No migration files found")
    
    def check_application_structure(self):
        """Check application structure."""
        print("\n🏗️ Application Structure Diagnostic...")
        
        # Check main application files
        critical_files = [
            "app/main.py",
            "app/__init__.py",
            "app/core/__init__.py",
            "app/modules/__init__.py"
        ]
        
        for file_path in critical_files:
            if Path(file_path).exists():
                self.log_finding("Structure", "OK", f"{file_path} exists")
            else:
                self.log_finding("Structure", "ERROR", f"{file_path} missing")
        
        # Check modules
        modules_dir = Path("app/modules")
        if modules_dir.exists():
            modules = [d for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
            self.log_finding("Structure", "OK", 
                           f"Application modules: {len(modules)}", 
                           {"modules": [m.name for m in modules]})
        else:
            self.log_finding("Structure", "ERROR", "Modules directory missing")
    
    def check_docker_status(self):
        """Check Docker status (safe)."""
        print("\n🐳 Docker Status Diagnostic...")
        
        try:
            # Check if docker command exists
            result = subprocess.run(['which', 'docker'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_finding("Docker", "OK", "Docker command available")
                
                # Check docker daemon (safe)
                result = subprocess.run(['docker', 'version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_finding("Docker", "OK", "Docker daemon running")
                else:
                    self.log_finding("Docker", "WARNING", "Docker daemon not accessible")
            else:
                self.log_finding("Docker", "WARNING", "Docker not installed")
                
        except subprocess.TimeoutExpired:
            self.log_finding("Docker", "WARNING", "Docker check timed out")
        except Exception as e:
            self.log_finding("Docker", "WARNING", f"Docker check failed: {e}")
    
    def check_ports_availability(self):
        """Check if required ports are available."""
        print("\n🌐 Port Availability Diagnostic...")
        
        required_ports = [8000, 5432, 6379, 3000]  # FastAPI, PostgreSQL, Redis, Frontend
        
        for port in required_ports:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.log_finding("Ports", "WARNING", f"Port {port} is in use")
                else:
                    self.log_finding("Ports", "OK", f"Port {port} is available")
                    
            except Exception as e:
                self.log_finding("Ports", "WARNING", f"Port {port} check failed: {e}")
    
    def generate_recommendations(self):
        """Generate safe recommendations based on findings."""
        print("\n📋 Generating Recommendations...")
        
        errors = [f for f in self.results["findings"] if f["status"] == "ERROR"]
        warnings = [f for f in self.results["findings"] if f["status"] == "WARNING"]
        
        if errors:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "category": "Critical Issues",
                "action": "Fix critical errors first",
                "details": f"Found {len(errors)} critical issues that must be resolved"
            })
        
        # Check for missing dependencies
        missing_deps = [f for f in self.results["findings"] 
                       if f["category"] == "Dependencies" and f["status"] == "ERROR"]
        if missing_deps:
            self.results["recommendations"].append({
                "priority": "HIGH", 
                "category": "Dependencies",
                "action": "Install missing Python packages",
                "command": "pip install -r requirements.txt"
            })
        
        # Check for Docker issues
        docker_issues = [f for f in self.results["findings"] 
                        if f["category"] == "Docker" and f["status"] != "OK"]
        if docker_issues:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Docker",
                "action": "Start Docker services",
                "command": "docker-compose up -d"
            })
        
        # Check for configuration issues
        config_issues = [f for f in self.results["findings"] 
                        if f["category"] == "Config" and f["status"] != "OK"]
        if config_issues:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Configuration", 
                "action": "Check configuration files",
                "details": "Ensure all configuration files are present and valid"
            })
    
    def run_diagnostic(self):
        """Run complete diagnostic in safe mode."""
        print("🛡️ Safe Connectivity Diagnostic Tool")
        print("=" * 50)
        print("🔒 SAFE MODE: No modifications will be made to your system")
        print("📊 Analyzing current state and connectivity issues...")
        
        # Run all checks
        self.check_python_environment()
        self.check_configuration_files()
        self.check_database_configuration()
        self.check_application_structure()
        self.check_docker_status()
        self.check_ports_availability()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        errors = len([f for f in self.results["findings"] if f["status"] == "ERROR"])
        warnings = len([f for f in self.results["findings"] if f["status"] == "WARNING"])
        ok_count = len([f for f in self.results["findings"] if f["status"] == "OK"])
        
        print(f"✅ OK: {ok_count}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"❌ Errors: {errors}")
        
        if errors == 0 and warnings <= 2:
            print("\n🎉 System looks healthy!")
            self.results["overall_status"] = "HEALTHY"
        elif errors == 0:
            print("\n✅ System is mostly healthy with minor issues")
            self.results["overall_status"] = "GOOD"
        elif errors <= 3:
            print("\n⚠️  System has some issues that need attention")
            self.results["overall_status"] = "NEEDS_ATTENTION"
        else:
            print("\n❌ System has significant issues")
            self.results["overall_status"] = "NEEDS_MAJOR_FIXES"
        
        # Print recommendations
        if self.results["recommendations"]:
            print("\n🎯 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"{i}. [{rec['priority']}] {rec['action']}")
                if 'command' in rec:
                    print(f"   Command: {rec['command']}")
                if 'details' in rec:
                    print(f"   Details: {rec['details']}")
        
        # Save results
        try:
            with open('diagnostic_results.json', 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Detailed results saved to: diagnostic_results.json")
        except Exception as e:
            print(f"\n⚠️  Could not save results: {e}")
        
        print("\n🛡️ Diagnostic completed safely - no system changes made")
        return self.results

if __name__ == "__main__":
    diagnostic = SafeConnectivityDiagnostic()
    results = diagnostic.run_diagnostic()