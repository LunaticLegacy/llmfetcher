"""Import every module exposed by the installed LLMFetcher wheel."""

from __future__ import annotations

import importlib
import pkgutil
import sys


def packaged_modules(package_name: str = "llmfetcher") -> list[str]:
    """Return the installed package and every recursively discoverable module.

    Args:
        package_name: Root import package to inspect. The default is the public
            LLMFetcher package installed from the wheel under test.

    Returns:
        Fully qualified module names, including the root package, sorted for a
        deterministic CI log.

    Raises:
        ImportError: If the root package cannot be imported from the installed
            distribution.
    """
    package = importlib.import_module(package_name)
    discovered = [package.__name__]
    if hasattr(package, "__path__"):
        discovered.extend(
            module.name
            for module in pkgutil.walk_packages(package.__path__, f"{package.__name__}.")
        )
    return sorted(set(discovered))


def import_modules(module_names: list[str]) -> list[tuple[str, BaseException]]:
    """Import each module and return failures without stopping at the first one.

    Args:
        module_names: Fully qualified module names to import in order.

    Returns:
        A list of `(module_name, exception)` pairs for modules that failed to
        import. An empty list means every module loaded successfully.
    """
    failures: list[tuple[str, BaseException]] = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except BaseException as error:  # report every broken module in one run
            failures.append((module_name, error))
    return failures


def main() -> int:
    """Run the packaged-module import check and print an actionable report."""
    module_names = packaged_modules()
    failures = import_modules(module_names)
    for module_name in module_names:
        status = "FAIL" if any(name == module_name for name, _ in failures) else "OK"
        print(f"{status}\t{module_name}")
    if failures:
        print("\nImport failures:", file=sys.stderr)
        for module_name, error in failures:
            print(f"- {module_name}: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(f"Imported {len(module_names)} packaged modules successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
