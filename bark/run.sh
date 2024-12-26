#!/bin/bash
set -x  # 디버그 모드 활성화
echo "Current directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "Updated PYTHONPATH: $PYTHONPATH"
uvicorn src.backend.main:app --reload