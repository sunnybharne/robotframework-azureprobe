# Contributing

Install Python, PowerShell 7, and the development dependencies:

```shell
python -m venv .venv
# Activate the environment using your shell's activation command.
python -m pip install -e '.[dev]'
python -m ruff check .
python -m pytest
python -m build
```

The offline tests do not require Az modules, an Azure account, or credentials.
They inject fake modules from `tests/fixtures/modules` into the PowerShell
processes for transport and error-path checks. Never add fixture behavior or
fake success paths to the production library.

For new keywords, document the arguments and failure behavior, then add tests
for meaningful success and error cases. Keep provider logic in the PowerShell
script and Robot assertions in Python. Pass arguments as structured data rather
than generating commands. Keep every cloud query tied to the requested
subscription and use process-scoped context changes.

Live checks are separate and opt-in: run `examples/vm_checks.robot` against an
existing test VM after signing in. Record Python, PowerShell, Az.Accounts, and
Az.Compute versions along with results. Do not commit contexts, credentials,
subscription-specific logs, or test output containing real infrastructure details.

Open a GitHub issue for bugs or proposals. Submit pull requests against `main`.
Update the changelog and keyword documentation when behavior changes.
