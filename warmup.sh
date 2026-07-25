#!/bin/bash
# ==============================================================================
# UFC Vision — Script Shell d'Exécution du Warm-up (DigitalOcean Cron / Systemd)
# ==============================================================================

# Obtenir le dossier racine du projet
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$PROJECT_DIR" || exit 1

# Création du dossier logs s'il n'existe pas
mkdir -p "$PROJECT_DIR/logs"

# Détection de l'environnement virtuel Python (.venv ou venv)
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_DIR/venv/bin/python"
else
    PYTHON_EXEC="$(which python3)"
fi

# Horodatage
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Executing UFC Vision Warm-up..." >> "$PROJECT_DIR/logs/warmup.log"

# Exécution du script Python warmup.py
$PYTHON_EXEC "$PROJECT_DIR/warmup.py" >> "$PROJECT_DIR/logs/warmup.log" 2>&1

echo "[$TIMESTAMP] Warm-up completed." >> "$PROJECT_DIR/logs/warmup.log"
