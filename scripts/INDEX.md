# llmfetcher/scripts/ — Packaging Checks INDEX

| File | Responsibility |
|---|---|
| `check_packaged_imports.py` | Imports every module exposed by the installed wheel and reports failures; invoked by `.github/workflows/ci.yml`. |

## Boundaries

- The check targets the installed distribution in a fresh environment, not the
  source checkout. Packaging membership is declared in `../pyproject.toml`.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [check_packaged_imports.py](check_packaged_imports.py#L10) | `packaged_modules` | `package_name: str` | `list[str]` | Return the installed package and every recursively discoverable module. |
| [check_packaged_imports.py](check_packaged_imports.py#L35) | `import_modules` | `module_names: list[str]` | `list[tuple[str, BaseException]]` | Import each module and return failures without stopping at the first one. |
| [check_packaged_imports.py](check_packaged_imports.py#L54) | `main` | `None` | `int` | Run the packaged-module import check and print an actionable report. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| — | — | `None` | `object` | 本索引范围不直接声明类；沿 Route Map 进入下级索引。 |

<!-- END GENERATED SYMBOL MAP -->
