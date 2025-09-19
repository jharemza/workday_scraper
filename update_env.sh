#!/bin/bash

set -euo pipefail

ENV_NAME="workday_scraper"
DATE_TAG=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="env_logs"
LOG_FILE="${LOG_DIR}/environment_${DATE_TAG}.yml"
OS_NAME=$(uname -s | tr '[:upper:]' '[:lower:]')

if [[ "$OS_NAME" == *"linux"* ]]; then
    # Linux-specific environment export
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
    fi

    LOG_FILE="${LOG_DIR}/environment_linux_${DATE_TAG}.yml"

    mkdir -p "$LOG_DIR"

    echo "[INFO] Exporting conda environment: $ENV_NAME"
    conda activate "$ENV_NAME"

    conda env export > environment_linux.yml
    conda env export > "$LOG_FILE"

    echo "[INFO] Updated environment_linux.yml"
    echo "[INFO] Snapshot saved to $LOG_FILE"
else
    # >>> Conda initialize (adjust path if needed) >>>
    __conda_setup="$('C:/Users/ubiqu/anaconda3/Scripts/conda.exe' 'shell.bash' 'hook' 2> /dev/null)"
    if [ $? -eq 0 ]; then
        eval "$__conda_setup"
    else
        export PATH="C:/Users/ubiqu/anaconda3/bin:$PATH"
    fi
    unset __conda_setup
    # <<< Conda initialize <<<

    mkdir -p "$LOG_DIR"

    echo "[INFO] Exporting conda environment: $ENV_NAME"
    conda activate "$ENV_NAME"

    conda env export > environment.yml
    conda env export > "$LOG_FILE"

    echo "[INFO] Updated environment.yml"
    echo "[INFO] Snapshot saved to $LOG_FILE"
fi
