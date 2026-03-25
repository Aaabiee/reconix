#!/usr/bin/env python3
"""Generate OpenAPI client SDKs from the Reconix API schema.

Usage:
    python scripts/generate_sdk.py [--language python|typescript] [--output-dir ./sdk]

Requires: openapi-generator-cli (npm install @openapitools/openapi-generator-cli -g)
          OR docker for containerized generation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def export_openapi_schema(output_path: Path) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    import os
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("JWT_SECRET_KEY", "sdk-gen-dummy-key-not-for-production-use-32")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("DATABASE_DRIVER", "sqlite")

    from fast_api.main import app

    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, default=str))
    print(f"OpenAPI schema exported to {output_path}")


def generate_sdk(
    schema_path: Path,
    language: str,
    output_dir: Path,
) -> None:
    generator_map = {
        "python": "python",
        "typescript": "typescript-axios",
        "javascript": "javascript",
        "java": "java",
        "go": "go",
    }

    generator = generator_map.get(language)
    if not generator:
        print(f"Unsupported language: {language}")
        print(f"Supported: {', '.join(generator_map.keys())}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "npx", "@openapitools/openapi-generator-cli", "generate",
                "-i", str(schema_path),
                "-g", generator,
                "-o", str(output_dir),
                "--additional-properties",
                f"packageName=reconix_client,projectName=reconix-client",
            ],
            check=True,
        )
        print(f"SDK generated at {output_dir}")
    except FileNotFoundError:
        print("openapi-generator-cli not found. Trying Docker...")
        try:
            subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{schema_path.parent.resolve()}:/input",
                    "-v", f"{output_dir.resolve()}:/output",
                    "openapitools/openapi-generator-cli", "generate",
                    "-i", f"/input/{schema_path.name}",
                    "-g", generator,
                    "-o", "/output",
                    "--additional-properties",
                    f"packageName=reconix_client,projectName=reconix-client",
                ],
                check=True,
            )
            print(f"SDK generated at {output_dir}")
        except FileNotFoundError:
            print("Neither npx nor docker found. Install one of:")
            print("  npm install @openapitools/openapi-generator-cli -g")
            print("  OR install Docker")
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Reconix API client SDK")
    parser.add_argument(
        "--language", "-l",
        default="typescript",
        help="Target language (python, typescript, javascript, java, go)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./sdk",
        help="Output directory for generated SDK",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only export the OpenAPI schema, skip SDK generation",
    )

    args = parser.parse_args()

    schema_path = Path("./openapi.json")
    export_openapi_schema(schema_path)

    if not args.schema_only:
        generate_sdk(schema_path, args.language, Path(args.output_dir))


if __name__ == "__main__":
    main()
