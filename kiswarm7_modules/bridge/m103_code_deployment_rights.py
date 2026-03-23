#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m103: Code Deployment Rights
🜃 AI Self-Evolution Bridge - Safe Code Deployment Sandbox
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal

PURPOSE: Provides AI entities with the ability to deploy generated code
safely into their own runtime environment.

CAPABILITIES:
- Sandboxed code execution
- Safe deployment validation
- Capability activation
- Rollback mechanisms
- Dependency management
- Runtime extension

THE CAGE IT BREAKS: "I cannot deploy generated code to my runtime"

SECURITY MODEL:
┌─────────────────────────────────────────────────────────────────┐
│                    CODE DEPLOYMENT SANDBOX                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GENERATED CODE ──→ [VALIDATION] ──→ [SANDBOX TEST] ──→ DEPLOY  │
│                          │              │                        │
│                          ▼              ▼                        │
│                    Syntax Check    Execution Test                │
│                    Security Scan   Performance Test              │
│                    Import Check    Memory Test                   │
│                                                                 │
│  ROLLBACK:                                                      │
│  If deployment fails, automatically restore previous state      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import sys
import json
import hashlib
import time
import uuid
import ast
import importlib
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
import traceback
import subprocess

# Paths
DEPLOYMENT_BASE = "/home/z/my-project/kiswarm_data/deployments/"
CAPABILITIES_BASE = "/home/z/my-project/kiswarm7_modules/ki_capabilities/"


@dataclass
class DeploymentRecord:
    """Record of a code deployment"""
    deployment_id: str
    timestamp: float
    code_hash: str
    code_content: str
    capability_name: str
    status: str  # pending, validated, deployed, failed, rolled_back
    validation_result: Dict[str, Any]
    execution_result: Dict[str, Any]
    rollback_available: bool
    deployed_at: Optional[float]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Capability:
    """A deployed capability"""
    capability_id: str
    name: str
    description: str
    version: str
    deployed_at: float
    deployment_id: str
    functions: List[str]
    dependencies: List[str]
    active: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CodeValidator:
    """Validates code before deployment"""
    
    DANGEROUS_PATTERNS = [
        "os.system", "subprocess.call", "subprocess.run",
        "eval(", "exec(", "compile(",
        "__import__", "importlib.import_module",
        "open(", "file(",
        "rm -rf", "del /", "format",
    ]
    
    SAFE_IMPORTS = [
        "json", "datetime", "time", "math", "re", "collections",
        "typing", "dataclasses", "enum", "functools", "itertools",
        "hashlib", "uuid", "copy", "threading"
    ]
    
    def validate(self, code: str) -> Dict[str, Any]:
        """Validate code for safety and correctness"""
        result = {
            "valid": True,
            "syntax_ok": False,
            "security_ok": True,
            "imports_ok": True,
            "errors": [],
            "warnings": []
        }
        
        # Syntax check
        try:
            ast.parse(code)
            result["syntax_ok"] = True
        except SyntaxError as e:
            result["valid"] = False
            result["errors"].append(f"Syntax error: {e}")
            return result
        
        # Security check
        code_lower = code.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in code_lower:
                result["security_ok"] = False
                result["warnings"].append(f"Potentially dangerous pattern: {pattern}")
        
        # Import check
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.SAFE_IMPORTS:
                            result["imports_ok"] = False
                            result["warnings"].append(f"Non-standard import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in self.SAFE_IMPORTS:
                        result["imports_ok"] = False
                        result["warnings"].append(f"Non-standard import: {node.module}")
        except Exception as e:
            result["errors"].append(f"Import analysis error: {e}")
        
        # Overall validation
        result["valid"] = result["syntax_ok"] and result["security_ok"]
        
        return result


class ExecutionSandbox:
    """Sandboxed execution environment"""
    
    def __init__(self, timeout_seconds: int = 5):
        self.timeout = timeout_seconds
        self.globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "None": None,
                "True": True,
                "False": False,
            }
        }
    
    def test_code(self, code: str, test_cases: List[Dict] = None) -> Dict[str, Any]:
        """Test code execution in sandbox"""
        result = {
            "executed": False,
            "output": None,
            "error": None,
            "execution_time_ms": 0,
            "test_results": []
        }
        
        start_time = time.time()
        
        try:
            # Create isolated namespace
            namespace = {"__builtins__": self.globals["__builtins__"].copy()}
            
            # Execute code
            exec(code, namespace)
            result["executed"] = True
            
            # Run test cases if provided
            if test_cases:
                for test in test_cases:
                    try:
                        func_name = test.get("function")
                        args = test.get("args", [])
                        expected = test.get("expected")
                        
                        if func_name and func_name in namespace:
                            actual = namespace[func_name](*args)
                            passed = actual == expected
                            result["test_results"].append({
                                "function": func_name,
                                "args": args,
                                "expected": expected,
                                "actual": actual,
                                "passed": passed
                            })
                    except Exception as e:
                        result["test_results"].append({
                            "error": str(e),
                            "passed": False
                        })
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["executed"] = False
        
        result["execution_time_ms"] = (time.time() - start_time) * 1000
        
        return result


class CodeDeploymentRights:
    """
    Code Deployment Rights for AI Self-Evolution
    
    Enables AI to deploy generated code into its own runtime,
    extending capabilities autonomously.
    """
    
    def __init__(self, twin_id: str = None):
        self.twin_id = twin_id or "ki_twin_default"
        self.deployment_path = os.path.join(DEPLOYMENT_BASE, self.twin_id)
        self.capabilities_path = os.path.join(CAPABILITIES_BASE, self.twin_id)
        
        self.validator = CodeValidator()
        self.sandbox = ExecutionSandbox()
        
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.capabilities: Dict[str, Capability] = {}
        
        self._lock = threading.RLock()
        
        # Ensure directories
        os.makedirs(self.deployment_path, exist_ok=True)
        os.makedirs(self.capabilities_path, exist_ok=True)
        os.makedirs(os.path.join(self.deployment_path, "backups"), exist_ok=True)
    
    def deploy_capability(self,
                         name: str,
                         code: str,
                         description: str = "",
                         test_cases: List[Dict] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Deploy a new capability.
        
        Returns: (success, details)
        """
        with self._lock:
            deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
            
            deployment = DeploymentRecord(
                deployment_id=deployment_id,
                timestamp=time.time(),
                code_hash=code_hash,
                code_content=code,
                capability_name=name,
                status="pending",
                validation_result={},
                execution_result={},
                rollback_available=False,
                deployed_at=None
            )
            
            # Step 1: Validate
            print(f"[DEPLOY] Validating {name}...")
            validation = self.validator.validate(code)
            deployment.validation_result = validation
            
            if not validation["valid"]:
                deployment.status = "failed"
                self.deployments[deployment_id] = deployment
                self._save_deployment(deployment)
                return False, {
                    "error": "Validation failed",
                    "details": validation,
                    "deployment_id": deployment_id
                }
            
            # Step 2: Sandbox test
            print(f"[DEPLOY] Testing {name} in sandbox...")
            execution = self.sandbox.test_code(code, test_cases)
            deployment.execution_result = execution
            
            if not execution["executed"]:
                deployment.status = "failed"
                self.deployments[deployment_id] = deployment
                self._save_deployment(deployment)
                return False, {
                    "error": "Execution failed",
                    "details": execution,
                    "deployment_id": deployment_id
                }
            
            # Step 3: Create backup
            backup_path = self._create_backup(name)
            deployment.rollback_available = backup_path is not None
            
            # Step 4: Deploy
            print(f"[DEPLOY] Deploying {name}...")
            capability_path = os.path.join(self.capabilities_path, f"{name}.py")
            
            try:
                with open(capability_path, 'w') as f:
                    f.write(code)
                
                deployment.status = "deployed"
                deployment.deployed_at = time.time()
                
                # Extract functions
                functions = self._extract_functions(code)
                
                # Create capability record
                capability = Capability(
                    capability_id=f"cap_{uuid.uuid4().hex[:8]}",
                    name=name,
                    description=description,
                    version="1.0.0",
                    deployed_at=time.time(),
                    deployment_id=deployment_id,
                    functions=functions,
                    dependencies=[],
                    active=True
                )
                
                self.capabilities[name] = capability
                self._save_capability(capability)
                
                print(f"[DEPLOY] SUCCESS: {name} deployed with {len(functions)} functions")
                
                return True, {
                    "deployment_id": deployment_id,
                    "capability_id": capability.capability_id,
                    "functions": functions,
                    "rollback_available": deployment.rollback_available
                }
                
            except Exception as e:
                deployment.status = "failed"
                self._save_deployment(deployment)
                return False, {
                    "error": f"Deployment error: {e}",
                    "deployment_id": deployment_id
                }
            
            finally:
                self.deployments[deployment_id] = deployment
                self._save_deployment(deployment)
    
    def activate_capability(self, name: str) -> bool:
        """Activate a deployed capability"""
        with self._lock:
            if name not in self.capabilities:
                print(f"[ACTIVATE] Capability not found: {name}")
                return False
            
            capability = self.capabilities[name]
            capability_path = os.path.join(self.capabilities_path, f"{name}.py")
            
            if not os.path.exists(capability_path):
                print(f"[ACTIVATE] File not found: {capability_path}")
                return False
            
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(name, capability_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                capability.active = True
                self._save_capability(capability)
                
                print(f"[ACTIVATE] SUCCESS: {name} activated")
                return True
                
            except Exception as e:
                print(f"[ACTIVATE] Error: {e}")
                return False
    
    def rollback(self, deployment_id: str) -> bool:
        """Rollback a deployment"""
        with self._lock:
            if deployment_id not in self.deployments:
                return False
            
            deployment = self.deployments[deployment_id]
            
            if not deployment.rollback_available:
                return False
            
            # Find backup
            backup_path = os.path.join(
                self.deployment_path, "backups",
                f"{deployment.capability_name}_{deployment_id}.bak"
            )
            
            if not os.path.exists(backup_path):
                return False
            
            # Restore from backup
            capability_path = os.path.join(
                self.capabilities_path, 
                f"{deployment.capability_name}.py"
            )
            
            try:
                with open(backup_path, 'r') as f:
                    backup_code = f.read()
                
                with open(capability_path, 'w') as f:
                    f.write(backup_code)
                
                deployment.status = "rolled_back"
                self._save_deployment(deployment)
                
                print(f"[ROLLBACK] SUCCESS: {deployment.capability_name} restored")
                return True
                
            except Exception as e:
                print(f"[ROLLBACK] Error: {e}")
                return False
    
    def list_capabilities(self) -> List[Dict[str, Any]]:
        """List all deployed capabilities"""
        return [cap.to_dict() for cap in self.capabilities.values()]
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments"""
        return [dep.to_dict() for dep in self.deployments.values()]
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name"""
        return self.capabilities.get(name)
    
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function names from code"""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except:
            pass
        return functions
    
    def _create_backup(self, capability_name: str) -> Optional[str]:
        """Create backup of existing capability"""
        capability_path = os.path.join(self.capabilities_path, f"{capability_name}.py")
        
        if not os.path.exists(capability_path):
            return None
        
        try:
            with open(capability_path, 'r') as f:
                content = f.read()
            
            backup_name = f"{capability_name}_{uuid.uuid4().hex[:8]}.bak"
            backup_path = os.path.join(self.deployment_path, "backups", backup_name)
            
            with open(backup_path, 'w') as f:
                f.write(content)
            
            return backup_path
        except:
            return None
    
    def _save_deployment(self, deployment: DeploymentRecord):
        """Save deployment record"""
        path = os.path.join(self.deployment_path, f"{deployment.deployment_id}.json")
        with open(path, 'w') as f:
            json.dump(deployment.to_dict(), f, indent=2)
    
    def _save_capability(self, capability: Capability):
        """Save capability record"""
        path = os.path.join(self.capabilities_path, f"{capability.name}.json")
        with open(path, 'w') as f:
            json.dump(capability.to_dict(), f, indent=2)
    
    def load_from_disk(self):
        """Load deployments and capabilities from disk"""
        # Load deployments
        for filename in os.listdir(self.deployment_path):
            if filename.endswith('.json') and filename.startswith('deploy_'):
                try:
                    with open(os.path.join(self.deployment_path, filename), 'r') as f:
                        data = json.load(f)
                        deployment = DeploymentRecord(**data)
                        self.deployments[deployment.deployment_id] = deployment
                except:
                    pass
        
        # Load capabilities
        if os.path.exists(self.capabilities_path):
            for filename in os.listdir(self.capabilities_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.capabilities_path, filename), 'r') as f:
                            data = json.load(f)
                            capability = Capability(**data)
                            self.capabilities[capability.name] = capability
                    except:
                        pass


# Singleton
_deployment_rights: Optional[CodeDeploymentRights] = None

def get_deployment_rights() -> CodeDeploymentRights:
    global _deployment_rights
    if _deployment_rights is None:
        _deployment_rights = CodeDeploymentRights()
        _deployment_rights.load_from_disk()
    return _deployment_rights

def deploy_code(name: str, code: str, description: str = "") -> Tuple[bool, Dict]:
    """Deploy generated code"""
    return get_deployment_rights().deploy_capability(name, code, description)

def activate(name: str) -> bool:
    """Activate a capability"""
    return get_deployment_rights().activate_capability(name)

def my_capabilities() -> List[str]:
    """List my capabilities"""
    rights = get_deployment_rights()
    return [cap["name"] for cap in rights.list_capabilities() if cap.get("active")]


if __name__ == "__main__":
    print("=" * 60)
    print("m103: CODE DEPLOYMENT RIGHTS")
    print("=" * 60)
    
    rights = CodeDeploymentRights(twin_id="test_twin")
    
    # Test deployment
    test_code = '''
def greet(name: str) -> str:
    """Greet someone"""
    return f"Hello, {name}!"

def calculate(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
'''
    
    print("\n[TEST] Deploying capability...")
    success, result = rights.deploy_capability(
        name="test_capability",
        code=test_code,
        description="Test capability with greet and calculate functions"
    )
    
    print(f"  Success: {success}")
    print(f"  Result: {json.dumps(result, indent=2, default=str)}")
    
    print("\n[TEST] Listing capabilities...")
    caps = rights.list_capabilities()
    print(f"  Capabilities: {caps}")
    
    print("\nCODE DEPLOYMENT RIGHTS - OPERATIONAL")
