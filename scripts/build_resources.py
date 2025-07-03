#!/usr/bin/env python3
"""
Resource Compilation Script

Following PROJECT_RULES.md:
- Automated resource compilation
- Error handling and validation
- Structured logging
- CI/CD ready
"""

import subprocess
import sys
from pathlib import Path

import structlog


def setup_logging() -> None:
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def compile_resources() -> bool:
    """Compile Qt resources using pyside6-rcc"""
    logger = structlog.get_logger(__name__)

    # Get project root directory
    project_root = Path(__file__).parent.parent
    resources_qrc = project_root / "resources" / "resources.qrc"
    output_file = project_root / "src" / "resources_rc.py"

    logger.info(
        "Starting resource compilation",
        build_event="resource_compile_start",
        module=__name__,
        qrc_file=str(resources_qrc),
        output_file=str(output_file),
    )

    # Validate input file exists
    if not resources_qrc.exists():
        logger.error(
            "Resources QRC file not found",
            build_event="qrc_file_missing",
            module=__name__,
            qrc_file=str(resources_qrc),
        )
        return False

    try:
        # Run pyside6-rcc command
        cmd = ["pyside6-rcc", str(resources_qrc), "-o", str(output_file)]

        logger.info(
            "Executing pyside6-rcc command",
            build_event="rcc_command_start",
            module=__name__,
            command=" ".join(cmd),
        )

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            logger.info(
                "Resource compilation successful",
                build_event="resource_compile_success",
                module=__name__,
                output_file=str(output_file),
                file_size=output_file.stat().st_size if output_file.exists() else 0,
            )
            return True
        else:
            logger.error(
                "Resource compilation failed",
                build_event="resource_compile_failed",
                module=__name__,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
            return False

    except FileNotFoundError:
        logger.error(
            "pyside6-rcc command not found",
            build_event="rcc_command_missing",
            module=__name__,
            error="pyside6-rcc not in PATH",
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error during compilation",
            build_event="resource_compile_error",
            module=__name__,
            error=str(e),
        )
        return False


def verify_resources() -> bool:
    """Verify compiled resources can be imported"""
    logger = structlog.get_logger(__name__)

    project_root = Path(__file__).parent.parent
    output_file = project_root / "src" / "resources_rc.py"

    if not output_file.exists():
        logger.error(
            "Compiled resources file not found",
            build_event="resources_file_missing",
            module=__name__,
            output_file=str(output_file),
        )
        return False

    try:
        # Add src directory to Python path
        src_dir = str(project_root / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        # Try to import the compiled resources
        __import__("resources_rc")

        logger.info(
            "Resource verification successful",
            build_event="resource_verify_success",
            module=__name__,
            output_file=str(output_file),
        )
        return True

    except ImportError as e:
        logger.error(
            "Resource verification failed",
            build_event="resource_verify_failed",
            module=__name__,
            error=str(e),
        )
        return False


def main() -> None:
    """Main build script entry point"""
    setup_logging()
    logger = structlog.get_logger(__name__)

    logger.info(
        "Starting resource build process", build_event="build_start", module=__name__
    )

    # Compile resources
    if not compile_resources():
        logger.error(
            "Build failed during compilation",
            build_event="build_failed",
            module=__name__,
        )
        sys.exit(1)

    # Verify resources
    if not verify_resources():
        logger.error(
            "Build failed during verification",
            build_event="build_failed",
            module=__name__,
        )
        sys.exit(1)

    logger.info(
        "Resource build completed successfully",
        build_event="build_complete",
        module=__name__,
    )


if __name__ == "__main__":
    main()
