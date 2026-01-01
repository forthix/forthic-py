"""
gRPC Server for Forthic
Implements stack-based execution and module discovery with configuration support
"""
import grpc
from concurrent import futures
import sys
import os
import asyncio
import traceback

# Import generated proto files
try:
    from forthic.grpc import forthic_runtime_pb2
    from forthic.grpc import forthic_runtime_pb2_grpc
    from forthic.grpc.serializer import serialize_value, deserialize_value
    from forthic.grpc.module_loader import load_modules_from_config, ModuleLoadError
except ImportError:
    print("Error: gRPC proto files not generated yet.")
    print("Run: make generate-grpc")
    sys.exit(1)

# Import Forthic interpreter
try:
    from forthic.interpreter import StandardInterpreter
except ImportError:
    print("Error: Could not import StandardInterpreter")
    sys.exit(1)

# Standard library modules (available in all runtimes)
STANDARD_MODULES = {
    "array", "record", "string", "math", "datetime", "json", "boolean"
}


class ForthicRuntimeServicer(forthic_runtime_pb2_grpc.ForthicRuntimeServicer):
    """Stack-based execution with module discovery and configuration support"""

    def __init__(self, modules_config: str | None = None):
        """
        Initialize the Forthic runtime server.

        Args:
            modules_config: Path to modules configuration YAML file.
                           If None, uses default behavior (pandas only).
        """
        # Create a StandardInterpreter instance
        self.interpreter = StandardInterpreter()

        # Track which runtime-specific modules are available
        self.runtime_modules = {}

        if modules_config:
            # Load modules from configuration file
            try:
                print(f"[SERVER] Loading modules from config: {modules_config}")
                loaded_modules = load_modules_from_config(modules_config)

                for name, mod_instance in loaded_modules.items():
                    self.interpreter.register_module(mod_instance)
                    self.runtime_modules[name] = mod_instance

                print(f"[SERVER] Loaded {len(loaded_modules)} module(s) from config")

            except ModuleLoadError as e:
                print(f"[SERVER] Failed to load modules: {e}")
                raise
        else:
            # Default behavior: Try to load pandas module if available
            # (backward compatible with existing behavior)
            try:
                from forthic.modules.pandas_module import PandasModule
                pandas_mod = PandasModule()
                self.interpreter.register_module(pandas_mod)
                self.runtime_modules['pandas'] = pandas_mod
            except ImportError:
                pass  # pandas not available

    def ExecuteWord(self, request, context):
        """Execute a word in the Python runtime using real interpreter"""
        try:
            word_name = request.word_name
            print(f"[EXECUTE_WORD] word='{word_name}' stack_size={len(request.stack)}", flush=True)

            # Deserialize the entire stack (all types)
            stack = [deserialize_value(sv) for sv in request.stack]
            print(f"[EXECUTE_WORD] Deserialized stack: {[type(x).__name__ for x in stack]}", flush=True)

            # Execute word with stack-based execution
            result_stack = asyncio.run(self._execute_with_stack(word_name, stack))
            print(f"[EXECUTE_WORD] Result stack: {[type(x).__name__ for x in result_stack]}", flush=True)

            # Serialize result stack
            response_stack = [serialize_value(v) for v in result_stack]
            print(f"[EXECUTE_WORD] Success", flush=True)

            return forthic_runtime_pb2.ExecuteWordResponse(result_stack=response_stack)

        except Exception as e:
            print(f"[EXECUTE_WORD] ERROR: {e}", flush=True)
            print(f"[EXECUTE_WORD] Traceback:", flush=True)
            traceback.print_exc()

            # Capture rich error context
            error = self._build_error_info(e, word_name)
            return forthic_runtime_pb2.ExecuteWordResponse(error=error)

    def ExecuteSequence(self, request, context):
        """
        Execute a sequence of words in one batch (optimization for remote execution)

        This is the batched execution optimization that reduces RPC round-trips.
        Instead of calling ExecuteWord multiple times, clients can send a sequence
        of word names and execute them all at once.
        """
        try:
            word_names = list(request.word_names)
            print(f"[EXECUTE_SEQUENCE] words={word_names} stack_size={len(request.stack)}", flush=True)

            # Deserialize the initial stack
            stack = [deserialize_value(sv) for sv in request.stack]
            print(f"[EXECUTE_SEQUENCE] Deserialized stack: {[type(x).__name__ for x in stack]}", flush=True)

            # Execute the word sequence
            result_stack = asyncio.run(self._execute_sequence_with_stack(word_names, stack))
            print(f"[EXECUTE_SEQUENCE] Result stack: {[type(x).__name__ for x in result_stack]}", flush=True)

            # Serialize result stack
            response_stack = [serialize_value(v) for v in result_stack]
            print(f"[EXECUTE_SEQUENCE] Success", flush=True)

            return forthic_runtime_pb2.ExecuteSequenceResponse(result_stack=response_stack)

        except Exception as e:
            print(f"[EXECUTE_SEQUENCE] ERROR: {e}", flush=True)
            print(f"[EXECUTE_SEQUENCE] Traceback:", flush=True)
            traceback.print_exc()

            # Capture rich error context
            # For sequences, we include the full word sequence in context
            error = self._build_error_info(e, word_name=None, context={'word_sequence': ', '.join(word_names)})
            return forthic_runtime_pb2.ExecuteSequenceResponse(error=error)

    def _build_error_info(self, exception: Exception, word_name: str = None, context: dict = None) -> 'forthic_runtime_pb2.ErrorInfo':
        """
        Build rich error information from an exception

        Args:
            exception: The exception that was raised
            word_name: The word that was being executed (optional)
            context: Additional context information (optional)

        Returns:
            ErrorInfo protobuf message with rich context
        """
        # Extract stack trace
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        stack_trace = [line.rstrip() for line in tb_lines]

        # Get error type name
        error_type = type(exception).__name__

        # Build context dictionary
        error_context = {}
        if word_name:
            error_context['word_name'] = word_name
        if context:
            error_context.update(context)

        # Try to extract module information from the traceback
        module_name = None
        word_location = None

        # Parse traceback to find Forthic-related frames
        for frame_summary in traceback.extract_tb(exception.__traceback__):
            filename = frame_summary.filename

            # Check if this is a Forthic module
            if 'forthic/modules/' in filename:
                module_name = filename.split('forthic/modules/')[-1].split('.')[0].replace('_module', '')
                word_location = f"{filename}:{frame_summary.lineno}"
                break
            elif 'forthic/grpc/' in filename:
                word_location = f"{filename}:{frame_summary.lineno}"

        # Build ErrorInfo message
        error_info = forthic_runtime_pb2.ErrorInfo(
            message=str(exception),
            runtime="python",
            stack_trace=stack_trace,
            error_type=error_type
        )


        # Add optional fields
        if word_location:
            error_info.word_location = word_location
        if module_name:
            error_info.module_name = module_name

        # Add context
        for key, value in error_context.items():
            error_info.context[key] = str(value)

        return error_info

    async def _execute_with_stack(self, word_name: str, stack: list) -> list:
        """
        Execute a word with given stack state
        Returns the resulting stack
        """
        # Create a fresh interpreter for this execution
        # (to avoid state pollution between requests)
        interp = StandardInterpreter()

        # Register runtime-specific modules in fresh interpreter
        for module_name, module in self.runtime_modules.items():
            interp.register_module(module)

        # Import all runtime-specific modules so their words are available
        if self.runtime_modules:
            module_names = list(self.runtime_modules.keys())
            interp.use_modules(module_names)

        # Push all stack items onto interpreter stack
        for item in stack:
            interp.stack_push(item)

        # Execute the word
        await interp.run(word_name)

        # Get resulting stack as a list
        result = interp.get_stack()
        # get_stack() returns a Stack object, convert to list
        return result.get_items()

    async def _execute_sequence_with_stack(self, word_names: list, stack: list) -> list:
        """
        Execute a sequence of words in one go (batched execution)

        Args:
            word_names: List of word names to execute in order
            stack: Initial stack state

        Returns:
            Final stack state after executing all words
        """
        # Create a fresh interpreter for this execution
        interp = StandardInterpreter()

        # Register runtime-specific modules
        for module_name, module in self.runtime_modules.items():
            interp.register_module(module)

        # Import all runtime-specific modules
        if self.runtime_modules:
            module_names_list = list(self.runtime_modules.keys())
            interp.use_modules(module_names_list)

        # Push all stack items onto interpreter stack
        for item in stack:
            interp.stack_push(item)

        # Execute each word in sequence
        for word_name in word_names:
            await interp.run(word_name)

        # Get resulting stack as a list
        result = interp.get_stack()
        return result.get_items()

    def ListModules(self, request, context):
        """List available runtime-specific modules (excludes stdlib)"""
        try:
            modules = []

            # Only return runtime-specific modules (not standard library)
            for name, mod in self.runtime_modules.items():
                # Get module metadata
                word_count = len([w for w in dir(mod) if w.isupper() and not w.startswith('_')])

                summary = forthic_runtime_pb2.ModuleSummary(
                    name=name,
                    description=f"Python-specific {name} module",
                    word_count=word_count,
                    runtime_specific=True
                )
                modules.append(summary)

            return forthic_runtime_pb2.ListModulesResponse(modules=modules)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error listing modules: {str(e)}")
            return forthic_runtime_pb2.ListModulesResponse()

    def GetModuleInfo(self, request, context):
        """Get detailed information about a specific module"""
        try:
            module_name = request.module_name

            if module_name not in self.runtime_modules:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Module '{module_name}' not found")
                return forthic_runtime_pb2.GetModuleInfoResponse()

            mod = self.runtime_modules[module_name]
            words = []

            # Use DecoratedModule.get_word_docs() if available (for decorated modules)
            if hasattr(mod, 'get_word_docs'):
                # DecoratedModule with @Word/@DirectWord decorators
                word_docs = mod.get_word_docs()
                for doc in word_docs:
                    word_info = forthic_runtime_pb2.WordInfo(
                        name=doc['name'],
                        stack_effect=doc['stackEffect'],
                        description=doc['description']
                    )
                    words.append(word_info)
            else:
                # Fallback: Extract word information from module using dir()
                for attr_name in dir(mod):
                    if attr_name.isupper() and not attr_name.startswith('_'):
                        word_info = forthic_runtime_pb2.WordInfo(
                            name=attr_name,
                            stack_effect="( -- )",
                            description=f"{attr_name} word from {module_name} module"
                        )
                        words.append(word_info)

            return forthic_runtime_pb2.GetModuleInfoResponse(
                name=module_name,
                description=f"Python-specific {module_name} module",
                words=words
            )

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting module info: {str(e)}")
            return forthic_runtime_pb2.GetModuleInfoResponse()


def serve(port=50051, modules_config: str | None = None):
    """
    Start the gRPC server

    Args:
        port: Port to listen on (default: 50051)
        modules_config: Path to modules configuration file (optional)
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Create servicer with optional config
    servicer = ForthicRuntimeServicer(modules_config=modules_config)

    forthic_runtime_pb2_grpc.add_ForthicRuntimeServicer_to_server(
        servicer, server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"Forthic Python gRPC server listening on port {port}")
    print("Configuration-based module loading")
    print("Features:")
    print("  - Full StandardInterpreter with all stdlib words")
    print("  - Runtime-specific module discovery (ListModules, GetModuleInfo)")

    if modules_config:
        print(f"  - Loaded modules from: {modules_config}")

    loaded = list(servicer.runtime_modules.keys())
    if loaded:
        print(f"  - Available runtime modules: {', '.join(loaded)}")
    else:
        print("  - No runtime-specific modules loaded")

    server.wait_for_termination()


def main():
    """
    CLI entry point for the Forthic gRPC server
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Forthic Python gRPC Runtime Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with default modules (pandas if available)
  python -m forthic.grpc.server

  # Start server with custom module configuration
  python -m forthic.grpc.server --modules-config /path/to/modules.yaml

  # Start on custom port
  python -m forthic.grpc.server --port 50052

  # Use environment variable for config
  export FORTHIC_MODULES_CONFIG=/etc/forthic/modules.yaml
  python -m forthic.grpc.server
        """
    )

    parser.add_argument(
        '--port',
        type=int,
        default=50051,
        help='Port to listen on (default: 50051)'
    )

    parser.add_argument(
        '--modules-config',
        type=str,
        default=None,
        help='Path to modules configuration YAML file'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='[::]',
        help='Host to bind to (default: [::] for all interfaces)'
    )

    args = parser.parse_args()

    # Check for environment variable if no config provided
    modules_config = args.modules_config
    if not modules_config:
        modules_config = os.getenv('FORTHIC_MODULES_CONFIG')

    serve(port=args.port, modules_config=modules_config)


if __name__ == "__main__":
    main()
