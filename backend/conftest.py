"""pytest conftest — ensures backend modules (universal, routes, services, …)
resolve to /app/backend/* and NOT to any same-named test sub-packages.

Without this, pytest inserts the tests/ dir into sys.path (because of the
tests/universal/__init__.py file), which causes `import universal` to resolve
to tests/universal/ instead of backend/universal/.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Push backend root to the very front of sys.path so it always wins.
sys.path = [_HERE] + [p for p in sys.path if p != _HERE]
