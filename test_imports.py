#!/usr/bin/env python3
"""Quick test to verify pack module imports work correctly."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🧪 Testing pack module imports...")
print(f"Python path: {sys.path[0]}")
print()

try:
    from pack import LLMFetcher, Agent, Tool
    print("✅ Core imports successful")
except ImportError as e:
    print(f"❌ Core import failed: {e}")
    sys.exit(1)

try:
    from pack.llm_fetcher import LLMBackendConfig
    print("✅ LLMBackendConfig import successful")
except ImportError as e:
    print(f"❌ LLMBackendConfig import failed: {e}")
    sys.exit(1)

try:
    from pack.swarm.swarm import AgentSwarm
    print("✅ AgentSwarm import successful")
except ImportError as e:
    print(f"❌ AgentSwarm import failed: {e}")
    sys.exit(1)

try:
    from pack.agent_io import AgentFileIOManager
    print("✅ AgentFileIOManager import successful")
except ImportError as e:
    print(f"❌ AgentFileIOManager import failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ All imports successful!")
print("=" * 60)
