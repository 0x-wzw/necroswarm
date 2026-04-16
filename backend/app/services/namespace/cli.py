#!/usr/bin/env python3
"""
OpenClaw Namespace CLI
Command-line interface for the OpenClaw namespace protocol.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from namespace import (
    NamespaceResolver, 
    URIParser, 
    resolve, 
    resolve_str,
    NAMESPACE_HANDLERS,
    DEFAULT_BASE_PATH
)


def cmd_resolve(args):
    """Resolve a URI to filesystem path."""
    resolver = NamespaceResolver(base_path=args.base)
    
    try:
        result = resolver.resolve(args.uri)
        print(result)
        
        # Optionally check if path exists
        if args.check:
            if result.exists():
                if result.is_file():
                    print(f"  ✓ File exists ({result.stat().st_size} bytes)", file=sys.stderr)
                elif result.is_dir():
                    print(f"  ✓ Directory exists", file=sys.stderr)
            else:
                print(f"  ✗ Path does not exist", file=sys.stderr)
                return 1
        
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_parse(args):
    """Parse and display URI components."""
    parser = URIParser()
    
    try:
        parsed = parser.parse(args.uri)
        
        print(f"URI: {parsed.raw}")
        print(f"Namespace: {parsed.namespace}")
        print(f"Path Parts: {parsed.path_parts}")
        print(f"Resource Type: {parsed.resource_type}")
        print(f"Resource ID: {parsed.resource_id or '(none)'}")
        
        if parsed.query:
            print(f"Query Parameters:")
            for k, v in parsed.query.items():
                print(f"  {k}={v}")
        
        if parsed.fragment:
            print(f"Fragment: {parsed.fragment}")
        
        # Show what it resolves to
        resolver = NamespaceResolver(base_path=args.base)
        try:
            path = resolver.resolve(args.uri)
            print(f"Resolves To: {path}")
        except ValueError:
            pass
        
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list_namespaces(args):
    """List all registered namespaces."""
    print("Registered Namespaces:")
    for ns, handler in sorted(NAMESPACE_HANDLERS.items()):
        doc = handler.__doc__ or "No description"
        # Get first line of docstring
        desc = doc.strip().split('\n')[0]
        print(f"  {ns:15} - {desc}")
    
    print(f"\nBase Path: {args.base or DEFAULT_BASE_PATH}")
    return 0


def cmd_validate(args):
    """Validate URIs from stdin or arguments."""
    uris = args.uris if args.uris else [line.strip() for line in sys.stdin if line.strip()]
    
    resolver = NamespaceResolver(base_path=args.base)
    errors = 0
    
    for uri in uris:
        if not uri.startswith("openclaw://"):
            print(f"✗ {uri} - Invalid protocol")
            errors += 1
            continue
        
        try:
            path = resolver.resolve(uri)
            status = "✓" if path.exists() else "~"
            print(f"{status} {uri} → {path}")
        except ValueError as e:
            print(f"✗ {uri} - {e}")
            errors += 1
    
    return 1 if errors else 0


def cmd_interactive(args):
    """Interactive shell for resolving URIs."""
    resolver = NamespaceResolver(base_path=args.base)
    
    print("OpenClaw Namespace Resolver - Interactive Mode")
    print("Enter URIs to resolve, or 'quit' to exit")
    print(f"Base Path: {resolver.base_path}")
    print()
    
    while True:
        try:
            uri = input("openclaw-ns> ").strip()
        except EOFError:
            break
        
        if not uri or uri.lower() in ('quit', 'exit', 'q'):
            break
        
        try:
            path = resolver.resolve(uri)
            exists = " [exists]" if path.exists() else ""
            print(f"→ {path}{exists}")
        except ValueError as e:
            print(f"Error: {e}")


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="openclaw-ns",
        description="OpenClaw Namespace Protocol - URI resolver for agent filesystems"
    )
    
    # Global options
    parser.add_argument(
        "--base", "-b",
        type=Path,
        default=None,
        help=f"Base path for resolution (default: {DEFAULT_BASE_PATH})"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # resolve command
    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Resolve a URI to filesystem path"
    )
    resolve_parser.add_argument("uri", help="The openclaw:// URI to resolve")
    resolve_parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Check if resolved path exists"
    )
    resolve_parser.set_defaults(func=cmd_resolve)
    
    # parse command
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse and display URI components"
    )
    parse_parser.add_argument("uri", help="The openclaw:// URI to parse")
    parse_parser.set_defaults(func=cmd_parse)
    
    # list command
    list_parser = subparsers.add_parser(
        "list",
        aliases=["ls"],
        help="List registered namespaces"
    )
    list_parser.set_defaults(func=cmd_list_namespaces)
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate URIs"
    )
    validate_parser.add_argument(
        "uris",
        nargs="*",
        help="URIs to validate (or read from stdin)"
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    # interactive command
    interactive_parser = subparsers.add_parser(
        "interactive",
        aliases=["i", "shell"],
        help="Interactive resolver shell"
    )
    interactive_parser.set_defaults(func=cmd_interactive)
    
    # Parse args
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())