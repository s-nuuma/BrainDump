#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
# カレントディレクトリ（BrainDumpルート）からの相対パスで実行できるように
PROJECT_ROOT=$(cd $(dirname $0); pwd)
cd "$PROJECT_ROOT"
"$@"
