#!/bin/bash
# ==============================================================================
# UFC Vision — Script de Déploiement Automatique (DigitalOcean)
# ==============================================================================

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$PROJECT_DIR" || exit 1

echo "🚀 Début du déploiement de UFC Vision..."

# 1. Annuler les modifications locales sur les fichiers de données régénérés par le bot
git checkout -- data/historical_tracker.json data/odds_cache.json 2>/dev/null || true

# 2. Récupérer le dernier code depuis GitHub
echo "📥 Récupération du code Git..."
git pull origin main

# 3. Lancer le chauffage de cache (Warmup)
echo "🔥 Exécution du chauffage de cache..."
if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    "$PROJECT_DIR/venv/bin/python" warmup.py --force
elif [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    "$PROJECT_DIR/.venv/bin/python" warmup.py --force
else
    python3 warmup.py --force
fi

# 4. Recharger Nginx et Streamlit
echo "🔄 Redémarrage des services..."
sudo systemctl reload nginx 2>/dev/null || true
sudo systemctl restart ufcvision 2>/dev/null || true

echo "✨ Déploiement terminé avec succès !"
