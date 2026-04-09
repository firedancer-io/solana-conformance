#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f "$REPO_ROOT/test_suite_env/bin/activate" ]; then
  # No venv -- skip (CI will catch issues)
  exit 0
fi

source "$REPO_ROOT/test_suite_env/bin/activate"
PYTHONPATH="$REPO_ROOT/src" python -c "
from test_suite.protos import invoke_pb2
from test_suite.flatbuffers_utils import FLATBUFFERS_AVAILABLE
print('imports OK')
" || {
  echo ""
  echo "ERROR: Python imports failed. Regenerate with: ./fetch_and_generate.sh"
  exit 1
}
