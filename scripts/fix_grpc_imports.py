#!/usr/bin/env python3
"""
Fix imports in generated gRPC files to use absolute imports
"""
import sys
from pathlib import Path

def fix_imports(file_path):
    """Fix the import statement in generated gRPC file"""
    content = file_path.read_text()

    # Replace relative import with absolute import
    old_import = "import forthic_runtime_pb2 as forthic__runtime__pb2"
    new_import = "from forthic.grpc import forthic_runtime_pb2 as forthic__runtime__pb2"

    if old_import in content:
        content = content.replace(old_import, new_import)
        file_path.write_text(content)
        print(f"Fixed imports in {file_path}")
        return True
    else:
        print(f"No fix needed for {file_path}")
        return False

if __name__ == "__main__":
    grpc_file = Path(__file__).parent.parent / "forthic" / "grpc" / "forthic_runtime_pb2_grpc.py"

    if not grpc_file.exists():
        print(f"Error: {grpc_file} not found")
        sys.exit(1)

    fix_imports(grpc_file)
