#!/usr/bin/env bash
# Upload vibephysics to PyPI. Requires a PyPI API token:
#   https://pypi.org/manage/account/token/
#
# Usage:
#   export PYPI_TOKEN='pypi-AgE...'
#   ./scripts/publish_pypi.sh
#
# Optional: upload to TestPyPI first:
#   PYPI_REPOSITORY=testpypi ./scripts/publish_pypi.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x /opt/homebrew/anaconda3/envs/py311/bin/python ]]; then
    PYTHON=/opt/homebrew/anaconda3/envs/py311/bin/python
  else
    PYTHON=python3
  fi
fi

TWINE="$("$PYTHON" -c 'import shutil; print(shutil.which("twine") or "")')"
if [[ -z "$TWINE" ]]; then
  "$PYTHON" -m pip install -q build twine
  TWINE="$PYTHON -m twine"
else
  TWINE="$TWINE"
fi

VERSION="$("$PYTHON" -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
echo "Package version: $VERSION"

if [[ ! -f "dist/vibephysics-${VERSION}-py3-none-any.whl" ]]; then
  echo "Building dist/vibephysics-${VERSION} ..."
  rm -rf dist build src/vibephysics.egg-info
  "$PYTHON" -m pip install -q build
  "$PYTHON" -m build
fi

$TWINE check "dist/vibephysics-${VERSION}"*

if [[ -z "${PYPI_TOKEN:-}" ]]; then
  echo "Error: set PYPI_TOKEN to your PyPI API token (pypi-AgE...)." >&2
  echo "  export PYPI_TOKEN='pypi-...'" >&2
  exit 1
fi

REPO="${PYPI_REPOSITORY:-pypi}"
if [[ "$REPO" == "testpypi" ]]; then
  UPLOAD_URL="https://test.pypi.org/legacy/"
  echo "Uploading to TestPyPI ..."
else
  UPLOAD_URL="https://upload.pypi.org/legacy/"
  echo "Uploading to PyPI ..."
fi

TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" \
  $TWINE upload --repository-url "$UPLOAD_URL" "dist/vibephysics-${VERSION}"*

echo ""
echo "Done. Verify:"
if [[ "$REPO" == "testpypi" ]]; then
  echo "  pip install -i https://test.pypi.org/simple/ vibephysics==${VERSION}"
else
  echo "  pip install -U vibephysics==${VERSION}"
  echo "  https://pypi.org/project/vibephysics/${VERSION}/"
fi
