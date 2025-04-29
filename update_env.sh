#!/bin/bash

# >>> Conda initialize (adjust path if needed) >>>
__conda_setup="$('C:/Users/ubiqu/anaconda3/Scripts/conda.exe' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    export PATH="C:/Users/ubiqu/anaconda3/bin:$PATH"
fi
unset __conda_setup
# <<< Conda initialize <<<

ENV_NAME="workday_scraper"
DATE_TAG=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="env_logs"
LOG_FILE="${LOG_DIR}/environment_${DATE_TAG}.yml"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "[INFO] Exporting conda environment: $ENV_NAME"
conda activate $ENV_NAME

# Export full and historical environment snapshots
conda env export > environment.yml
conda env export > "$LOG_FILE"

echo "[INFO] Updated environment.yml"
echo "[INFO] Snapshot saved to $LOG_FILE"
