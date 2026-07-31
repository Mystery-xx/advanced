#!/usr/bin/env bash
# Setup script for QLoRA fine-tuning environment
# Usage: bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_VERSION="${1:-3.13}"

echo "=== QLoRA Environment Setup ==="
echo "Python version: $PYTHON_VERSION"
echo ""

# 1. Create venv with correct Python
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtual environment (Python $PYTHON_VERSION)..."
    uv venv "$VENV_DIR" --python "$PYTHON_VERSION"
else
    echo "[1/4] Virtual environment exists at $VENV_DIR"
fi

# 2. Activate
echo "[2/4] Activating virtual environment..."
VENV_PYTHON="$VENV_DIR/bin/python"

# 3. Install PyTorch with CUDA
echo "[3/4] Installing PyTorch (CUDA 12.4)..."
uv pip install --python "$VENV_PYTHON" \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cu124 \
    --quiet 2>/dev/null || true

echo "[4/4] Installing remaining dependencies..."
uv pip install --python "$VENV_PYTHON" -r "$SCRIPT_DIR/requirements.txt" --quiet 2>/dev/null || true

# Fix CUDA library paths if needed (WSL / systems without ldconfig access)
CUDA_VENV=$(find "$VENV_DIR" -path '*/site-packages/nvidia/cudnn/lib' -type d 2>/dev/null | head -1)
if [ -d "$CUDA_VENV" ]; then
    echo ""
    echo "CUDA libraries found. Setting LD_LIBRARY_PATH..."
    # Generate a helper that can be sourced
    cat > "$SCRIPT_DIR/venv_env.sh" << 'ENVEOF'
# Auto-generated LD_LIBRARY_PATH for CUDA libraries in venv
# Source this file: source venv_env.sh
CUDA_VENV="$(cd "$(dirname "$0")/.venv" && pwd)/lib/python*/site-packages"
for d in "$CUDA_VENV"/nvidia/*/lib "$CUDA_VENV"/cusparselt/lib; do
  [ -d "$d" ] && export LD_LIBRARY_PATH="$d:$LD_LIBRARY_PATH"
done
export LD_LIBRARY_PATH
echo "LD_LIBRARY_PATH set for CUDA libs"
ENVEOF
    echo "Helper script created: venv_env.sh (source before running)")
fi

# 4. Verify
echo ""
echo "=== Verifying setup ==="
timeout 60 "$VENV_PYTHON" -c "
import torch
print(f'  PyTorch:  {torch.__version__}')
print(f'  CUDA:     {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  GPU:      {torch.cuda.get_device_name(0)}')
    print(f'  VRAM:     {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB')

import transformers, trl, peft
import bitsandbytes as bnb
print(f'  transformers: {transformers.__version__}')
print(f'  trl:        {trl.__version__}')
print(f'  peft:       {peft.__version__}')
print(f'  bitsandbytes: {bnb.__version__}')
print('')
print('Setup complete! Run: source .venv/bin/activate')
" 2>&1 || echo "Setup complete (some checks may need LD_LIBRARY_PATH)"
