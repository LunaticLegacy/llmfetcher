# Semantic map

## `scripts.check_packaged_imports`

| Symbol | Responsibility | Calls / called by |
| --- | --- | --- |
| `packaged_modules` | Imports the installed root package and recursively discovers every package module with `pkgutil`. | Called by `main`. |
| `import_modules` | Imports all discovered modules while collecting every failure instead of stopping at the first exception. | Called by `main`. |
| `main` | Prints one status line per module and exits non-zero when any import fails. | Script entry point; invoked by `.github/workflows/ci.yml`. |

## Packaging relationship

`llmfetcher.rag_module_tlb` is explicitly listed in `pyproject.toml` so the
wheel contains the full TLB module tree. The CI check imports the wheel from a
fresh virtual environment, not the source checkout.
