# Release procedure

1. Update the version in `pyproject.toml`, `src/AzureProbe/__init__.py`, and the
   `@library` decorator in `src/AzureProbe/keywords.py`.
2. Update `CHANGELOG.md`, the release notes, and documentation.
3. Run lint, offline tests (including real PowerShell), and an opt-in live check
   against a test subscription. Record the tested runtime/module versions.
4. Build with `python -m build`. Install the wheel in a fresh virtual environment
   and verify that it includes `AzureProbe/scripts/Get-AzureVm.ps1` and imports
   correctly in Robot Framework.
5. Confirm PyPI name availability and configure the publishing account. Validate
   the distribution on TestPyPI before publishing to PyPI. Refer to the
   [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
6. After publication, update the README installation instructions and create a
   matching GitHub tag and release. The existing release notes are a draft only.
7. Request a Robot Framework directory listing through an issue or pull request
   in the [website repository](https://github.com/robotframework/robotframework.github.com).
   Include the library name, a description of at most 200 characters, and its URL.

Suggested directory description:

> Robot Framework library for checking Azure virtual machine configuration, tags, and power state through Azure PowerShell.
