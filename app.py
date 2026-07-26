"""
UFC Vision — High-End MMA Analytics & Prediction Platform
Garantit la protection intégrale et l'inviolabilité du backend (src/, models/, data/).
Interface 100% HTML/CSS pure avec bulles Blanc Pur, sélecteur de langue discret et conformité légale intégrale.
"""

import os
import sys
import json
import base64
import datetime
import collections
import joblib
import pandas as pd
import numpy as np
import streamlit as st

# Garantie d'inclusion du dossier racine et du dossier src dans sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Imports Robustes des Modules Backend (SOC - Intact)
try:
    from src.predict import (
        load_resources_v3, resolve_fighter_name, compute_fighter_dynamic_states_v3,
        get_latest_fighter_profile_v3, STAT_COLS_V1, FEATURE_COLS_V3
    )
    from src.odds_api import get_cached_or_fresh_odds
    from src.utils import normalize_fighter_name, fuzzy_match_fighter_name
    from src.historical_tracker import sync_historical_tracker, deduplicate_card_fights
except ImportError:
    from predict import (
        load_resources_v3, resolve_fighter_name, compute_fighter_dynamic_states_v3,
        get_latest_fighter_profile_v3, STAT_COLS_V1, FEATURE_COLS_V3
    )
    from odds_api import get_cached_or_fresh_odds
    from utils import normalize_fighter_name, fuzzy_match_fighter_name
    from historical_tracker import sync_historical_tracker, deduplicate_card_fights

# Helper pour récupérer l'image logo (logo.jpg) sous forme base64
def get_logo_data_url():
    logo_path = os.path.join(project_root, "logo.jpg")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as img_f:
                encoded = base64.b64encode(img_f.read()).decode("utf-8")
                return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            pass
    return "https://ufcvision.com/logo.jpg"

# Helper pour récupérer l'URL de l'image Open Graph avec Cache-Busting automatique (mtime)
def get_og_image_url():
    og_path = os.path.join(project_root, "og-image.jpg")
    if os.path.exists(og_path):
        mtime = int(os.path.getmtime(og_path))
        return f"https://ufcvision.com/og-image.jpg?v={mtime}"
    return "https://ufcvision.com/og-image.jpg?v=1"

# DICTIONNAIRE CENTRALISÉ DE TRADUCTIONS ET TEXTES JURIDIQUES / FAQ (EN / FR / ES)
LANG_DATA = {
    "EN": {
        "page_title": "UFC Vision - MMA Analytics & Predictions",
        "nav_past": "📜 Past Fights",
        "nav_home": "🥊 UFC Vision",
        "nav_upcoming": "🔮 Upcoming Fights",
        "nav_legal": "⚖️ Legal Notice & Privacy Policy",
        "back_home": "← Back to Home",
        "hero_subtitle": "The Premier UFC Prediction Bot",
        "hero_description": "UFC Vision is an independent project by MMA data enthusiasts, not affiliated with the UFC. Our model analyzes over 20 statistical factors per matchup based on 10 years of fight history.",
        "stat_winrate_desc": "Bot Winrate (2015 - 2026)",
        "stat_roi_desc": "Bot ROI (2015 - 2026)",
        "upcoming_title": "🔮 Upcoming UFC Event Predictions",
        "select_upcoming_card": "Select an upcoming UFC card:",
        "insufficient_data": "🔘 INSUFFICIENT DATA — Incomplete UFC history.",
        "odds_pending": "⏳ ODDS PENDING — Awaiting official odds.",
        "high_confidence": "🟢 VALUE OPPORTUNITY: {fighter}",
        "insufficient_confidence": "🚨 NO VALUE DETECTED",
        "global_summary_title": "🌐 Global Performance",
        "card_summary_title": "📅 Event Performance",
        "past_title": "📊 Real Performance (10€ Simulated Stake)",
        "net_profit": "💵 Total Net Profit",
        "roi_yield": "📈 ROI Yield",
        "win_rate": "🎯 Win Rate",
        "staked_vol": "💶 Volume Staked",
        "select_past_card": "Select a past UFC event:",
        "won_text": "gained",
        "bets_text": "bets",
        "won_pill": "🟢 WON (+{gain} €) — Successful bet on {fighter} (Odds: {odds}). Winner: {winner}.",
        "lost_pill": "🔴 LOST (-10.00 €) — Bet placed on {fighter} (Odds: {odds}). Winner: {winner}.",
        "no_bet_eval": "⚪ NO BET — No Value Bet (EV max: {ev}%)",
        "no_bet_desc": "Avoided bet: Insufficient value. Winner: {winner}.",
        "void_pill": "⚪ CANCELLED / VOID — Fight did not take place (Stake refunded)",
        "odds_freshness": "⚡ Odds updated {mins} mins ago from The Odds API",
        "bug_contact": "✉️ Found a bug or have a question? contact@auradev.fr",
        # FAQ EN
        "faq_title": "❓ Frequently Asked Questions (FAQ)",
        "q1": "How does UFC Vision's AI work?",
        "a1": "Our XGBoost V3 algorithm evaluates over 20 differential statistical factors between two fighters (ELO score gaps, strike output, takedown defense rate, win streaks, recent rankings, etc.) built upon 10 years of historical UFC fight data.",
        "q2": "Where do fight data and odds come from?",
        "a2": "Fight statistics are extracted from official UFC fight archives, while market odds are fetched in real-time through global bookmaker aggregator APIs.",
        "q3": "What is a Value Opportunity?",
        "a3": "A Value Opportunity indicates that the AI-calculated probability shows a significant statistical edge (Value) when matched against published market odds.",
        "q4": "Is UFC Vision affiliated with the UFC?",
        "a4": "No. UFC Vision is an independent analytical project created by MMA data enthusiasts. We are not affiliated with, sponsored by, or endorsed by UFC or TKO Group Holdings.",
        "faq_contact": "Have more questions? Feel free to contact us at contact@auradev.fr",
        # JURIDIQUE EN
        "legal_page_title": "⚖️ Legal Notice, Privacy Policy & Cookie Management",
        "legal_sec1_title": "1. Site Publisher & Legal Notice",
        "legal_sec2_title": "2. Cloud Infrastructure & Hosting",
        "legal_sec3_title": "3. Intellectual Property & Anti-Scraping",
        "legal_sec4_title": "4. Data Privacy Policy & GDPR Compliance",
        "legal_sec5_title": "5. AI & Financial Disclaimer",
        "legal_sec6_title": "6. Responsible Gaming (+18)",
        "legal_sec7_title": "7. Trademark & Independence Notice",
        "legal_sec8_title": "8. Advertising Networks & Monetization",
        "legal_publisher": "<b>Publisher:</b> UFC Vision (https://ufcvision.com) is published by Aura Dev (SIRET: 10542993000016 — Legal Anonymity Protection under Art. 6-III-2 of French LCEN Law n° 2004-575). Contact: contact@auradev.fr",
        "legal_hosting": "<b>Cloud Host:</b> DigitalOcean LLC | 101 Avenue of the Americas, 10th Floor, New York, NY 10013, USA | Web: https://www.digitalocean.com | Phone: +1 888-892-2732 | Support: support@digitalocean.com",
        "legal_ip": "<b>Intellectual Property:</b> All Machine Learning models (XGBoost V3), algorithms, interface designs, and code powering UFC Vision are the exclusive intellectual property of Aura Dev. Automated data scraping or commercial reproduction is strictly prohibited.",
        "legal_privacy": "<b>Privacy & Cookies:</b> UFC Vision does not require account registration or process direct personal identification data. We utilize Google Tag Manager, Google Analytics 4, and third-party ad networks (such as Google AdSense) that place cookies to measure audience and deliver relevant ads.",
        "legal_ads": "<b>Advertisements:</b> This platform displays programmatic advertisements and affiliate content. Ad network partners may collect non-identifiable technical browsing data to optimize ad relevancy.",
        "disclaimer_ai": "<b>AI Disclaimer:</b> UFC Vision is an analytical decision-support tool. Predictions are strictly for informational purposes and do not constitute financial advice or sports betting recommendations. No outcome is guaranteed, and Aura Dev disclaims all liability for losses incurred.",
        "disclaimer_gaming": "<b>Responsible Gaming (+18):</b> Sports betting is strictly prohibited for minors. Gambling involves financial debt, isolation, and addiction risks. Please gamble responsibly.",
        "disclaimer_trademark": "<b>Trademark & Independence Notice:</b> UFC Vision is an independent analytics project created by MMA data enthusiasts, published by Aura Dev. We analyze public UFC data and are in no way affiliated with, authorized, sponsored, or endorsed by UFC or TKO Group Holdings.",
        # COOKIES EN
        "cookie_dialog_title": "🍪 Cookie Preferences & Privacy",
        "cookie_title": "Cookie & Privacy Preferences",
        "cookie_desc": "UFC Vision uses essential technical cookies, anonymous audience analytics (Google Analytics / GTM), and advertising cookies to keep the service free.",
        "cookie_accept": "Accept All Cookies",
        "cookie_decline": "Essential Only",
        "footer": "UFC Vision © 2026 — All Rights Reserved | Published by Aura Dev (SIRET: 10542993000016)"
    },
    "FR": {
        "page_title": "UFC Vision — Analyse MMA de Haute Précision",
        "nav_past": "📜 Combats Antérieurs",
        "nav_home": "🥊 UFC Vision",
        "nav_upcoming": "🔮 Combats Futurs",
        "nav_legal": "⚖️ Mentions Légales & Confidentialité",
        "back_home": "← Retour à l'accueil",
        "hero_subtitle": "Le meilleur bot de prédiction de l'UFC",
        "hero_description": "UFC Vision est un projet indépendant conçu par des passionnés de MMA, non affilié à l'UFC. Notre modèle analyse plus de 20 facteurs statistiques par combat sur 10 ans d'historique.",
        "stat_winrate_desc": "Winrate du bot (2015 - 2026)",
        "stat_roi_desc": "ROI du bot (2015 - 2026)",
        "upcoming_title": "🔮 Prédictions des Prochains Événements UFC",
        "select_upcoming_card": "Sélectionnez une carte UFC à venir :",
        "insufficient_data": "🔘 DONNÉES INSUFFISANTES — Historique UFC incomplet.",
        "odds_pending": "⏳ COTES EN ATTENTE — En attente des cotes officielles.",
        "high_confidence": "🟢 OPPORTUNITÉ DÉTECTÉE : {fighter}",
        "insufficient_confidence": "🚨 AUCUNE OPPORTUNITÉ INTÉRESSANTE",
        "global_summary_title": "🌐 Bilan Global",
        "card_summary_title": "📅 Bilan de cette soirée",
        "past_title": "📊 Performance Réelle (Mise Fictive 10 €)",
        "net_profit": "💵 Profit Net Total",
        "roi_yield": "📈 Rendement ROI",
        "win_rate": "🎯 Taux de Réussite",
        "staked_vol": "💶 Volume Misé",
        "select_past_card": "Sélectionnez une soirée UFC passée :",
        "won_text": "gagnés",
        "bets_text": "paris",
        "won_pill": "🟢 GAGNÉ (+{gain} €) — Pari réussi sur {fighter} (Cote : {odds}). Vainqueur : {winner}.",
        "lost_pill": "🔴 PERDU (-10.00 €) — Pari engagé sur {fighter} (Cote : {odds}). Vainqueur : {winner}.",
        "no_bet_eval": "⚪ NO BET — Pas de Value Bet (EV max : {ev}%)",
        "no_bet_desc": "Pari évité : Valeur insuffisante. Vainqueur : {winner}.",
        "void_pill": "⚪ ANNULÉ / VOID — Combat non disputé (Pari remboursé)",
        "odds_freshness": "⚡ Cotes actualisées il y a {mins} min via The Odds API",
        "bug_contact": "✉️ Une question ou une erreur à signaler ? contact@auradev.fr",
        # FAQ FR
        "faq_title": "❓ Foire Aux Questions (FAQ)",
        "q1": "Comment fonctionne l'intelligence artificielle d'UFC Vision ?",
        "a1": "Notre algorithme XGBoost V3 compare simultanément plus de 20 variables statistiques ajustées entre deux combattants (différentiels d'ELO, volume de coups, efficacité de défense de takedown, séries de victoires, classement récent, etc.) sur les 10 dernières années de combats UFC.",
        "q2": "D'où proviennent les données et les cotes ?",
        "a2": "Les métriques de combat sont issues de l'historique officiel de l'UFC, et les cotes sont récupérées en temps réel via des APIs agrégatrices de bookmakers mondiaux.",
        "q3": "Qu'est-ce qu'une Opportunité Détectée (Value Bet) ?",
        "a3": "Une opportunité détectée indique que la probabilité calculée par l'IA présente un écart statistique avantageux (Value) par rapport à la cote proposée sur le marché.",
        "q4": "UFC Vision est-il affilié à l'UFC ?",
        "a4": "Non. UFC Vision est un projet d'analyse indépendant créé par des passionnés de MMA. Il n'est en aucun cas affilié, sponsorisé ou approuvé par l'UFC ou TKO Group Holdings.",
        "faq_contact": "Vous avez d me d'autres questions ? N'hésitez pas à nous contacter à contact@auradev.fr",
        # JURIDIQUE FR
        "legal_page_title": "⚖️ Mentions Légales, Politique de Confidentialité & Gestion des Cookies",
        "legal_sec1_title": "1. Éditeur du site & Mentions Légales",
        "legal_sec2_title": "2. Hébergement & Infrastructure Cloud",
        "legal_sec3_title": "3. Propriété Intellectuelle & Protection des Données",
        "legal_sec4_title": "4. Politique de Confidentialité & Conformité RGPD",
        "legal_sec5_title": "5. Avertissement IA & Non-Responsabilité Financière",
        "legal_sec6_title": "6. Jeu Responsable & Protection des Mineurs (+18)",
        "legal_sec7_title": "7. Indépendance de Marque & Passionnés",
        "legal_sec8_title": "8. Régies Publicitaires & Monétisation",
        "legal_publisher": "<b>Éditeur du site :</b> Le site UFC Vision (https://ufcvision.com) est édité par l'entreprise Aura Dev (SIRET : 10542993000016 — Dispositif de protection d'anonymat légal - Art. 6-III-2 de la Loi LCEN n° 2004-575). Contact : contact@auradev.fr",
        "legal_hosting": "<b>Hébergement Cloud :</b> DigitalOcean LLC | 101 Avenue of the Americas, 10th Floor, New York, NY 10013, États-Unis | Site : https://www.digitalocean.com | Tél : +1 888-892-2732 | Support : support@digitalocean.com",
        "legal_ip": "<b>Propriété Intellectuelle :</b> L'ensemble des modèles de Machine Learning (XGBoost V3), algorithmes, interfaces et code source sont la propriété exclusive d'Aura Dev. Toute aspiration automatisée de données (scraping) ou réutilisation commerciale est strictly interdite.",
        "legal_privacy": "<b>Données Personnelles & Cookies :</b> UFC Vision ne requiert la création d'aucun compte et ne collecte aucune donnée nominative directe. Des outils de mesure d'audience (Google Tag Manager, Google Analytics 4) et des régies publicitaires tierces (Google AdSense) utilisent des cookies pour analyser le trafic et diffuser des annonces pertinentes.",
        "legal_ads": "<b>Annonces Publicitaires :</b> Le site héberge des espaces publicitaires. Les régies partenaires traitent des données techniques d'affichage non identifiables pour adapter la pertinence des publicités.",
        "disclaimer_ai": "<b>Avertissement IA :</b> UFC Vision est un outil d'aide à la décision. Les prédictions sont fournies à titre pur informatif. Aucun gain n'est garanti et Aura Dev décline toute responsabilité en cas de pertes liées à l'utilisation du service.",
        "disclaimer_gaming": "<b>Jeu Responsable (+18) :</b> Les paris sportifs sont strictly interdits aux mineurs. Jouer comporte des risques : endettement, isolement, dépendance. Contactez Joueurs Info Service au 09 74 75 13 13.",
        "disclaimer_trademark": "<b>Avertissement de Marque & Indépendance :</b> UFC Vision est un projet d'analyse indépendant conçu par des passionnés de MMA et édité par Aura Dev. Nous analysons les données publiques de l'UFC et ne sommes en aucun cas affiliés, autorisés, sponsorisés ou approuvés par l'UFC ou TKO Group Holdings.",
        # COOKIES FR
        "cookie_dialog_title": "🍪 Préférences des Cookies",
        "cookie_title": "Gestion des Cookies & Confidentialité",
        "cookie_desc": "UFC Vision utilise des cookies techniques, de mesure d'audience anonyme (Google Analytics / GTM) et publicitaires pour maintenir le service gratuit.",
        "cookie_accept": "Tout Accepter",
        "cookie_decline": "Essentiels Uniquement",
        "footer": "UFC Vision © 2026 — Tous droits réservés | Édité par Aura Dev (SIRET : 10542993000016)"
    },
    "ES": {
        "page_title": "UFC Vision — Analítica de MMA de Alta Gama",
        "nav_past": "📜 Combates Anteriores",
        "nav_home": "🥊 UFC Vision",
        "nav_upcoming": "🔮 Próximos Combates",
        "nav_legal": "⚖️ Aviso Legal y Privacidad",
        "back_home": "← Volver al Inicio",
        "hero_subtitle": "El mejor bot de predicción de la UFC",
        "hero_description": "UFC Vision es un proyecto independiente creado por apasionados de las MMA, no afiliado a la UFC. Nuestro modelo analiza más de 20 factores por pelea basados en 10 años de datos.",
        "stat_winrate_desc": "Tasa de victoria del bot (2015 - 2026)",
        "stat_roi_desc": "ROI del bot (2015 - 2026)",
        "upcoming_title": "🔮 Predicciones de Próximos Eventos UFC",
        "select_upcoming_card": "Seleccione una cartelera de la UFC:",
        "insufficient_data": "🔘 DATOS INSUFFICIENTES — Historial de UFC incompleto.",
        "odds_pending": "⏳ CUOTAS PENDIENTES — Esperando cuotas oficiales.",
        "high_confidence": "🟢 OPORTUNIDAD DETECTADA: {fighter}",
        "insufficient_confidence": "🚨 SIN OPORTUNIDAD DE VALOR",
        "global_summary_title": "🌐 Rendimiento Global",
        "card_summary_title": "📅 Rendimiento de esta velada",
        "past_title": "📊 Rendimiento Real (Apuesta Simulada 10 €)",
        "net_profit": "💵 Beneficio Neto Total",
        "roi_yield": "📈 Rendimiento ROI",
        "win_rate": "🎯 Tasa de Acierto",
        "staked_vol": "💶 Volumen Apostado",
        "select_past_card": "Seleccione un evento pasado de UFC:",
        "won_text": "ganados",
        "bets_text": "apuestas",
        "won_pill": "🟢 GANADO (+{gain} €) — Apuesta con éxito en {fighter} (Cuota: {odds}). Ganador: {winner}.",
        "lost_pill": "🔴 PERDIDO (-10.00 €) — Apuesta realizada en {fighter} (Cuota: {odds}). Ganador: {winner}.",
        "no_bet_eval": "⚪ NO BET — Sin Value Bet (EV máx: {ev}%)",
        "no_bet_desc": "Apuesta evitada: Valor insuficiente. Ganador: {winner}.",
        "void_pill": "⚪ CANCELADO / VOID — Combate no disputado (Apuesta reembolsada)",
        "odds_freshness": "⚡ Cuotas actualizadas hace {mins} min via The Odds API",
        "bug_contact": "✉️ ¿Tienes alguna duda o error que reportar? contact@auradev.fr",
        # FAQ ES
        "faq_title": "❓ Preguntas Frecuentes (FAQ)",
        "q1": "¿Cómo funciona la IA de UFC Vision?",
        "a1": "Nuestro algoritmo XGBoost V3 analiza más de 20 variables estadísticas comparativas entre dos peleadores (diferencial de ELO, golpes por minuto, defensa de derribos, racha de victorias, etc.) basándose en 10 años de datos de la UFC.",
        "q2": "¿De dónde proceden los datos y las cuotas?",
        "a2": "Las estadísticas se extraen de los archivos oficiales de la UFC y las cuotas se recopilan en tiempo real mediante APIs agregadoras internacionales.",
        "q3": "¿Qué es una Oportunidad de Valor (Value Bet)?",
        "a3": "Una oportunidad detectada indica que la probabilidad calculada por la IA ofrece una ventaja estadística (Valor) respecto a la cuota publicada por el mercado.",
        "q4": "¿Está UFC Vision afiliado a la UFC?",
        "a4": "No. UFC Vision es un proyecto analítico independiente creado por apasionados de las MMA. No está afiliado, patrocinado ni respaldado por la UFC o TKO Group Holdings.",
        "faq_contact": "¿Tienes más preguntas? No dudes en contactarnos en contact@auradev.fr",
        # JURIDIQUE ES
        "legal_page_title": "⚖️ Aviso Legal, Política de Privacidad y Cookies",
        "legal_sec1_title": "1. Editor del sitio y Aviso Legal",
        "legal_sec2_title": "2. Alojamiento e Infraestructura",
        "legal_sec3_title": "3. Propiedad Intelectual y Scraping",
        "legal_sec4_title": "4. Privacidad de Datos y Cumplimiento RGPD",
        "legal_sec5_title": "5. Exención de Responsabilidad IA",
        "legal_sec6_title": "6. Juego Responsable (+18)",
        "legal_sec7_title": "7. Independencia de Marca y Aficionados",
        "legal_sec8_title": "8. Redes Publicitarias",
        "legal_publisher": "<b>Editor del sitio:</b> UFC Vision (https://ufcvision.com) es editado por Aura Dev (SIRET: 10542993000016 — Protección legal de anonimato Art. 6-III-2 Ley LCEN). Contacto: contact@auradev.fr",
        "legal_hosting": "<b>Alojamiento Cloud:</b> DigitalOcean LLC | 101 Avenue of the Americas, 10th Floor, New York, NY 10013, EE. UU. | Web: https://www.digitalocean.com | Tel: +1 888-892-2732 | Contacto: support@digitalocean.com",
        "legal_ip": "<b>Propiedad Intelectual:</b> Todos los modelos de Machine Learning (XGBoost V3), algoritmos y código son propiedad exclusiva de Aura Dev. Se prohíbe la extracción automatizada de datos (scraping).",
        "legal_privacy": "<b>Privacidad y Cookies:</b> UFC Vision no requiere creación de cuenta. Utilizamos Google Tag Manager, Google Analytics 4 y redes publicitarias (Google AdSense) que pueden utilizar cookies para medir el tráfico.",
        "legal_ads": "<b>Anuncios:</b> Este sitio web muestra publicidad programática y enlaces de afiliación para financiar la plataforma.",
        "disclaimer_ai": "<b>Aviso de IA:</b> UFC Vision es una herramienta de soporte analítico. Las predicciones son informativas y no constituyen asesoramiento financiero ni recomendación de apuestas.",
        "disclaimer_gaming": "<b>Juego Responsable (+18):</b> Las apuestas deportivas están prohibidas para menores. El juego conlleva riesgos de adicción y endeudamiento.",
        "disclaimer_trademark": "<b>Aviso de Marca e Independencia:</b> UFC Vision es un proyecto analítico independiente creado por apasionados de las MMA y editado por Aura Dev. Analizamos datos públicos de la UFC y no estamos en ningún caso afiliados, autorizados, patrocinados ni respaldados por la UFC o TKO Group Holdings.",
        # COOKIES ES
        "cookie_dialog_title": "🍪 Preferencias de Cookies",
        "cookie_title": "Preferencia de Cookies y Privacidad",
        "cookie_desc": "UFC Vision utiliza cookies técnicas, de medición de audiencia anónima (Google Analytics / GTM) y anuncios adaptados.",
        "cookie_accept": "Aceptar Todo",
        "cookie_decline": "Solo Esenciales",
        "footer": "UFC Vision © 2026 — Todos los derechos reservados | Editado por Aura Dev (SIRET: 10542993000016)"
    }
}


def render_clean_html(html_str):
    """Supprime tous les espaces d'indentation au début de chaque ligne HTML."""
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# 1. Configuration de la Page Streamlit (Open Graph / Favicon & Titre)
st.set_page_config(
    page_title="UFC Vision - MMA Analytics & Predictions",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chargement de la source image du Logo (logo.jpg)
logo_data_url = get_logo_data_url()

# 2. Design System "Aura Dev" CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
    
    /* Masquer le header, la toolbar et TOUS les widgets de statut/spinners Streamlit */
    [data-testid="stHeader"], header, #MainMenu, footer,
    [data-testid="stStatusWidget"], div[data-testid="stStatusWidget"],
    [data-testid="stSpinner"], div[data-testid="stSpinner"], div.stSpinner,
    .stStatusWidget, [data-testid="stNotification"],
    div[data-testid="stStatusContainer"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    /* Annuler tout le rembourrage supérieur de la page */
    [data-testid="stAppViewContainer"] > .main, 
    .main .block-container, 
    div[data-testid="stMainBlockContainer"] {{
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        padding-bottom: 2rem !important;
        max-width: 1050px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        color: #1E293B;
    }}
    
    /* Fond général du site : GRIS CLAIR #F1F5F9 */
    .stApp, 
    [data-testid="stAppViewContainer"], 
    body {{
        background-color: #F1F5F9 !important;
        background: #F1F5F9 !important;
    }}

    /* CENTRAGE ET ABAISSEMENT DU POP-UP COOKIE (@st.dialog) */
    div[data-testid="stDialog"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    div[data-testid="stDialog"] > div {{
        margin-top: 18vh !important;
        border-radius: 28px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18) !important;
    }}

    /* MASQUER STRICTEMENT LA CROIX DE FERMETURE DU POP-UP COOKIE (@st.dialog) */
    div[data-testid="stDialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] button[data-testid="stDialogCloseButton"],
    div[role="dialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] header button,
    div[data-testid="stDialog"] [data-testid="stBaseButton-headerNoPadding"] {{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}

    /* MINI-PILULE DE LANGUE FIXÉE STRICTEMENT AU COIN SUPÉRIEUR DROIT */
    div[data-testid="stSelectbox"]:has(*[aria-label="lang_select_hidden"]) {{
        position: fixed !important;
        top: 12px !important;
        right: 20px !important;
        width: 82px !important;
        max-width: 82px !important;
        z-index: 999999 !important;
    }}

    div[data-testid="stSelectbox"]:has(*[aria-label="lang_select_hidden"]) > div > div {{
        border-radius: 9999px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08) !important;
        font-family: 'Noto Color Emoji', 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.25rem !important;
        padding-left: 8px !important;
        padding-right: 4px !important;
        min-height: 38px !important;
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    div[data-testid="stSelectbox"]:has(*[aria-label="lang_select_hidden"]) * {{
        font-family: 'Noto Color Emoji', 'Plus Jakarta Sans', sans-serif !important;
    }}

    /* Style des 3 boutons pilules du header principal */
    .stButton > button {{
        border-radius: 9999px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 0.5rem !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100% !important;
        display: block !important;
        text-align: center !important;
    }}

    .stButton > button:hover {{
        border-color: #3D3EEA !important;
        color: #3D3EEA !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(61, 62, 234, 0.12) !important;
    }}

    /* Intégration du Logo dans la pilule de navigation centrale (UFC Vision) */
    div[data-testid="stColumn"]:has(button[key="btn_nav_home"]) button {{
        background-image: url("{logo_data_url}") !important;
        background-size: contain !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        color: transparent !important;
        min-height: 42px !important;
    }}

    /* CLASSES SPECIFIQUES POUR LES BULLES BLANC PUR #FFFFFF */
    .fight-card-pure-white, .summary-card-pure-white, .legal-card-pure-white {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
    }}

    /* ACCORDÉONS HAUTE QUALITÉ */
    details.aura-accordion {{
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 16px 22px !important;
        margin-top: 14px !important;
        text-align: left !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03) !important;
    }}

    details.aura-accordion summary {{
        font-weight: 800 !important;
        color: #1E293B !important;
        cursor: pointer !important;
        font-size: 0.98rem !important;
        outline: none !important;
    }}

    details.aura-accordion p, details.aura-accordion div {{
        font-size: 0.88rem !important;
        color: #475569 !important;
        margin-top: 12px !important;
        line-height: 1.6 !important;
    }}

    /* Badges de combat */
    .pill-main-red {{
        background-color: #D20A0A !important;
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }}

    .pill-comain-dark {{
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }}

    /* Action Signal Pills */
    .signal-pill-rec {{
        background-color: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        border-left: 6px solid #10B981 !important;
        color: #065F46 !important;
        padding: 0.9rem 1.2rem;
        border-radius: 18px;
        font-weight: 700;
        margin-top: 0.8rem;
    }}

    .signal-pill-no {{
        background-color: #FFF7ED !important;
        border: 1px solid #FFEDD5 !important;
        border-left: 6px solid #F97316 !important;
        color: #9A3412 !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }}

    .signal-pill-wait {{
        background-color: #FEFCE8 !important;
        border: 1px solid #FEF08A !important;
        border-left: 6px solid #EAB308 !important;
        color: #854D0E !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }}

    .signal-pill-none {{
        background-color: #F0F9FF !important;
        border: 1px solid #BAE6FD !important;
        border-left: 6px solid #3B82F6 !important;
        color: #075985 !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }}

    /* Result Pills */
    .result-pill-win {{
        background-color: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        color: #065F46 !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        margin-top: 0.8rem !important;
    }}

    .result-pill-loss {{
        background-color: #FEF2F2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #991B1B !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        margin-top: 0.8rem !important;
    }}

    .result-pill-nobet {{
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #475569 !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.88rem !important;
        margin-top: 0.8rem !important;
    }}

    /* HERO BUBBLE TEXTE */
    .hero-bubble-text {{
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 36px !important;
        padding: 2.5rem 2.5rem !important;
        text-align: center !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important;
        margin: 2rem auto 2.5rem auto !important;
    }}

    .stat-pill {{
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 32px !important;
        padding: 2rem 1.5rem !important;
        text-align: center !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03) !important;
    }}

    .stat-val-huge {{
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #3D3EEA;
        line-height: 1;
        margin-bottom: 0.5rem;
    }}

    .stat-desc-clean {{
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569;
    }}

    .footer-aura {{
        text-align: center;
        padding: 2rem 0 2.5rem 0;
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# FONCTION POP-UP DIALOG COOKIE NATIVE STREAMLIT
# =========================================================================

@st.dialog("🍪 Cookie Preferences")
def show_cookie_dialog(t):
    st.markdown(f"#### {t['cookie_title']}")
    st.write(t['cookie_desc'])
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_dec, col_acc = st.columns(2)
    with col_dec:
        if st.button(t["cookie_decline"], key="dlg_btn_decline", use_container_width=True):
            st.session_state["cookie_consent"] = "declined"
            st.query_params["cookie_consent"] = "declined"
            st.rerun()
    with col_acc:
        if st.button(t["cookie_accept"], key="dlg_btn_accept", use_container_width=True):
            st.session_state["cookie_consent"] = "accepted"
            st.query_params["cookie_consent"] = "accepted"
            st.rerun()


# =========================================================================
# FONCTIONS DE CACHING STREAMLIT HAUTE PERFORMANCE
# =========================================================================

@st.cache_resource(show_spinner=False)
def load_all_models_and_data():
    """Mise en cache du modèle XGBoost V3 et des structures de données statiques."""
    return load_resources_v3()


@st.cache_data(ttl=7200, show_spinner=False)
def get_cached_odds_data():
    """Mise en cache 2h des cotes The Odds API."""
    return get_cached_or_fresh_odds()


@st.cache_resource(show_spinner=False)
def get_cached_tracker_data(events, _raw_df, _model, _medians, _all_fighters):
    """Mise en cache instantanée du tracker d'historique (Lecture directe disque pré-chauffé)."""
    tracker_path = os.path.join("data", "historical_tracker.json")
    if os.path.exists(tracker_path):
        try:
            with open(tracker_path, "r", encoding="utf-8") as f:
                tracker_data = json.load(f)

            cards_map = tracker_data.get("cards", {})
            summary = tracker_data.get("summary", {})

            if cards_map and summary:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                upcoming_cards = collections.OrderedDict()
                past_cards = collections.OrderedDict()

                sorted_card_keys = sorted(cards_map.keys())
                for k in sorted_card_keys:
                    c_info = cards_map[k]
                    c_date = c_info.get("event_date", "")
                    is_comp = c_info.get("is_completed", False)

                    if is_comp or c_date < today_str:
                        past_cards[k] = c_info
                    else:
                        upcoming_cards[k] = c_info

                past_cards_reversed = collections.OrderedDict(reversed(list(past_cards.items())))
                return upcoming_cards, past_cards_reversed, summary
        except Exception:
            pass

    return sync_historical_tracker(events, _raw_df, _model, _medians, _all_fighters)


@st.cache_resource(show_spinner=False)
def get_cached_dynamic_states(_raw_df):
    """Mise en cache du calcul des ELOs."""
    return compute_fighter_dynamic_states_v3(_raw_df)


@st.cache_resource(show_spinner=False)
def get_cached_fighter_profile(name, _raw_df, _elo_dict, _history_dict, _win_streak_dict, _loss_streak_dict, _latest_rank_dict):
    """Mise en cache du profil et des caractéristiques d'un combattant."""
    return get_latest_fighter_profile_v3(name, _raw_df, _elo_dict, _history_dict, _win_streak_dict, _loss_streak_dict, _latest_rank_dict)


def extract_fight_odds(ev, name_a, name_b):
    """Extrait les cotes réelles sans altérer le moteur."""
    if ev.get("odds_a") and ev.get("odds_b") and float(ev.get("odds_a", 0.0)) > 1.0 and float(ev.get("odds_b", 0.0)) > 1.0:
        return float(ev["odds_a"]), float(ev["odds_b"]), ev.get("bkm_name", "Bookmakers Officiels")

    bookmakers = ev.get("bookmakers", [])
    if not bookmakers:
        return None, None, None

    f1_raw = ev.get("home_team", ev.get("f1", ""))
    f2_raw = ev.get("away_team", ev.get("f2", ""))
    targets = [t for t in [name_a, name_b, f1_raw, f2_raw] if t]

    best_o_a, best_o_b, best_bkm = None, None, None

    for bkm in bookmakers:
        bkm_name = bkm.get("title", bkm.get("key", "Bookmaker"))
        for mkt in bkm.get("markets", []):
            if mkt.get("key") == "h2h":
                outcomes = mkt.get("outcomes", [])
                omap = {}
                for o in outcomes:
                    oname = o.get("name", "")
                    oprice = float(o.get("price", 0.0))
                    if oname and oprice > 1.0:
                        matched = fuzzy_match_fighter_name(oname, targets, threshold=0.70)
                        if matched:
                            omap[matched] = oprice

                o_a = omap.get(name_a) or omap.get(f1_raw)
                o_b = omap.get(name_b) or omap.get(f2_raw)

                if o_a and o_b:
                    if best_o_a is None or (o_a + o_b > best_o_a + best_o_b):
                        best_o_a, best_o_b, best_bkm = o_a, o_b, bkm_name

    return best_o_a, best_o_b, best_bkm


def main():
    # 🌐 SÉLECTEUR DE LANGUE ISOLÉ (Drapeaux uniquement, pilule discrète tout en haut à droite)
    lang_map = {"🇬🇧": "EN", "🇫🇷": "FR", "🇪🇸": "ES"}
    reverse_lang_map = {"EN": "🇬🇧", "FR": "🇫🇷", "ES": "🇪🇸"}

    current_lang = st.session_state.get("lang", "EN")
    default_flag = reverse_lang_map.get(current_lang, "🇬🇧")

    selected_flag = st.selectbox(
        "lang_select_hidden",
        options=["🇬🇧", "🇫🇷", "🇪🇸"],
        index=["🇬🇧", "🇫🇷", "🇪🇸"].index(default_flag),
        label_visibility="collapsed",
        key="sb_language_flags"
    )
    st.session_state["lang"] = lang_map[selected_flag]

    current_lang = st.session_state["lang"]
    t = LANG_DATA.get(current_lang, LANG_DATA["EN"])

    # Session State Router
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "home"

    # 🖼️ INJECTION DES BALISES META OPEN GRAPH DYNAMIQUES AVEC CACHE-BUSTING AUTOMATIQUE (?v=timestamp)
    og_img_url = get_og_image_url()
    st.components.v1.html(f"""
    <script>
    try {{
        const doc = window.parent.document;
        const metaTags = [
            {{ property: 'og:title', content: 'UFC Vision — MMA Analytics & Predictions' }},
            {{ property: 'og:description', content: 'Premier UFC Prediction Bot powered by XGBoost V3.' }},
            {{ property: 'og:image', content: '{og_img_url}' }},
            {{ property: 'og:url', content: 'https://ufcvision.com' }},
            {{ property: 'og:type', content: 'website' }},
            {{ name: 'twitter:card', content: 'summary_large_image' }},
            {{ name: 'twitter:title', content: 'UFC Vision — MMA Analytics & Predictions' }},
            {{ name: 'twitter:description', content: 'Premier UFC Prediction Bot powered by XGBoost V3.' }},
            {{ name: 'twitter:image', content: '{og_img_url}' }}
        ];
        metaTags.forEach(t => {{
            let attr = t.property ? 'property' : 'name';
            let val = t.property || t.name;
            let elem = doc.querySelector(`meta[${{attr}}="${{val}}"]`);
            if (!elem) {{
                elem = doc.createElement('meta');
                elem.setAttribute(attr, val);
                doc.head.appendChild(elem);
            }}
            elem.setAttribute('content', t.content);
        }});
    }} catch(e) {{}}
    </script>
    """, height=0, width=0)

    # 🍪 SÉCURISATION & PERSISTANCE DU CONSENTEMENT COOKIE (QUERY PARAMS + LOCALSTORAGE)
    if "cookie_consent" in st.query_params:
        st.session_state["cookie_consent"] = st.query_params["cookie_consent"]

    # Script JS de persistance localStorage pour préserver le choix lors de la réactualisation F5
    st.components.v1.html("""
    <script>
    try {
        const parentWin = window.parent;
        const urlParams = new URLSearchParams(parentWin.location.search);
        const consent = urlParams.get('cookie_consent');
        if (consent) {
            parentWin.localStorage.setItem('ufc_cookie_consent', consent);
        } else {
            const saved = parentWin.localStorage.getItem('ufc_cookie_consent');
            if (saved) {
                const url = new URL(parentWin.location.href);
                url.searchParams.set('cookie_consent', saved);
                parentWin.location.replace(url.toString());
            }
        }
    } catch(e) {}
    </script>
    """, height=0, width=0)

    # DECLENCHEMENT POP-UP DIALOG COOKIES NATIVE SI PAS ENCORE DE CONSENTEMENT ENREGISTRÉ
    if "cookie_consent" not in st.session_state:
        show_cookie_dialog(t)

    # Chargement Backend Intact
    events, from_cache, age_hours = get_cached_odds_data()
    odds_age_mins = max(1, int(age_hours * 60))

    try:
        model, raw_df, medians, all_fighters, model_path_used = load_all_models_and_data()
    except Exception as e:
        st.error(f"Erreur d'initialisation du modèle : {e}")
        st.stop()

    upcoming_cards, past_cards, fin_summary = get_cached_tracker_data(events, raw_df, model, medians, all_fighters)
    elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = get_cached_dynamic_states(raw_df)

    # 🏛️ BANDEAU DE NAVIGATION PARFAITEMENT CENTRÉ AU MILIEU EXACT DU SITE (STRICTEMENT 3 BOUTONS)
    c_pad_l, c_nav_box, c_pad_r = st.columns([0.7, 2.6, 0.7])

    with c_nav_box:
        c_left, c_center, c_right = st.columns([1.35, 1.0, 1.35])

        with c_left:
            if st.button(t["nav_past"], key="btn_nav_past", use_container_width=True):
                st.session_state["current_page"] = "past"
                st.rerun()

        with c_center:
            if st.button(t["nav_home"], key="btn_nav_home", use_container_width=True):
                st.session_state["current_page"] = "home"
                st.rerun()

        with c_right:
            if st.button(t["nav_upcoming"], key="btn_nav_upcoming", use_container_width=True):
                st.session_state["current_page"] = "upcoming"
                st.rerun()

    # Stylisation dynamique de la pilule active
    current_page = st.session_state.get("current_page", "home")
    if current_page == "past":
        active_btn_key = "btn_nav_past"
    elif current_page == "upcoming":
        active_btn_key = "btn_nav_upcoming"
    else:
        active_btn_key = "btn_nav_home"

    st.markdown(f"""
    <style>
        div[data-testid="stColumn"]:has(button[key="{active_btn_key}"]) button {{
            border-color: #3D3EEA !important;
            box-shadow: 0 4px 14px rgba(61, 62, 234, 0.18) !important;
            font-weight: 800 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    page = current_page

    # =========================================================================
    # PAGE 1 : 🏠 ACCUEIL (BULLE LOGO UNIQUE ALIGNÉE + BULLE TEXTE ÉCARTÉE + STATS + FAQ)
    # =========================================================================
    if page == "home":
        # BULLE 1 : LE LOGO GÉANT SEUL EN BULLE BLANCHE
        render_clean_html(f"""
        <div style="background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 36px !important; overflow: hidden !important; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important; margin: 3.5rem auto 2rem auto !important; text-align: center !important;">
            <img src="{logo_data_url}" alt="UFC Vision Logo" style="width: 100%; height: auto; display: block; border-radius: 36px;">
        </div>
        """)

        # BULLE 2 : LE TEXTE DE PRÉSENTATION CLAIREMENT ÉCARTÉ
        render_clean_html(f"""
        <div class="hero-bubble-text">
            <p style="font-size: 1.35rem; font-weight: 700; color: #0F172A; margin: 0 0 0.8rem 0;">
                {t['hero_subtitle']}
            </p>
            <p style="font-size: 1.05rem; font-weight: 500; color: #475569; margin: 0 auto; max-width: 780px; line-height: 1.65;">
                {t['hero_description']}
            </p>
        </div>
        """)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            render_clean_html(f"""
            <div class="stat-pill">
                <div class="stat-val-huge">69 %</div>
                <div class="stat-desc-clean">{t['stat_winrate_desc']}</div>
            </div>
            """)

        with col_m2:
            render_clean_html(f"""
            <div class="stat-pill">
                <div class="stat-val-huge">+31 %</div>
                <div class="stat-desc-clean">{t['stat_roi_desc']}</div>
            </div>
            """)

        # SECTION FAQ
        render_clean_html(f"""
        <div style="margin-top: 3.5rem;">
            <details class="aura-accordion">
                <summary><b>{t['faq_title']}</b></summary>
                <div style="padding-top: 10px;">
                    <p style="margin-bottom: 12px;"><b>{t['q1']}</b><br>{t['a1']}</p>
                    <p style="margin-bottom: 12px;"><b>{t['q2']}</b><br>{t['a2']}</p>
                    <p style="margin-bottom: 12px;"><b>{t['q3']}</b><br>{t['a3']}</p>
                    <p style="margin-bottom: 12px;"><b>{t['q4']}</b><br>{t['a4']}</p>
                    <p style="margin-top: 14px; font-weight: 600; color: #3D3EEA;">{t['faq_contact']}</p>
                </div>
            </details>
        </div>
        """)

    # =========================================================================
    # PAGE 2 : 🔮 COMBATS FUTURS
    # =========================================================================
    elif page == "upcoming":
        st.markdown(f"### {t['upcoming_title']}")

        render_clean_html(f"""
        <div style="margin-bottom: 1rem; font-size: 0.85rem; font-weight: 600; color: #64748B;">
            {t['odds_freshness'].format(mins=odds_age_mins)}
        </div>
        """)

        if not upcoming_cards:
            st.info("ℹ️ No upcoming card available.")
        else:
            chronological_keys = list(upcoming_cards.keys())

            selected_card_key = st.selectbox(
                t["select_upcoming_card"],
                chronological_keys,
                format_func=lambda k: f"🗓️ {k} ({len(upcoming_cards[k].get('fights', []))} fights)",
                key="sb_upcoming"
            )

            card_info = upcoming_cards[selected_card_key]
            selected_events = deduplicate_card_fights(card_info.get("fights", []))

            for idx, ev in enumerate(selected_events, 1):
                f1_raw = ev.get("f1") or ev.get("home_team", "")
                f2_raw = ev.get("f2") or ev.get("away_team", "")
                fight_label = ev.get("fight_label", f"Fight #{idx}")

                name_a = resolve_fighter_name(f1_raw, all_fighters)
                name_b = resolve_fighter_name(f2_raw, all_fighters)

                profile_a = get_cached_fighter_profile(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None
                profile_b = get_cached_fighter_profile(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_b else None

                odds_a, odds_b, bkm_name = extract_fight_odds(ev, name_a or f1_raw, name_b or f2_raw)

                has_full_data = bool(name_a and name_b and profile_a is not None and profile_b is not None)
                has_valid_odds = bool(odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0)

                badge_html = ""
                if fight_label == "MAIN EVENT":
                    badge_html = '<span class="pill-main-red">🔥 MAIN EVENT</span>'
                elif fight_label == "CO-MAIN EVENT":
                    badge_html = '<span class="pill-comain-dark">⭐ CO-MAIN EVENT</span>'

                if not has_full_data:
                    signal_html = f'<div class="signal-pill-none">{t["insufficient_data"]}</div>'
                    html_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
{signal_html}
</div>"""
                    render_clean_html(html_card)
                    continue

                try:
                    delta_dict = {}
                    for stat in STAT_COLS_V1:
                        delta_key = f"delta_{stat}"
                        val_a, val_b = profile_a[stat], profile_b[stat]
                        delta_dict[delta_key] = (val_a - val_b) if (pd.notna(val_a) and pd.notna(val_b)) else medians.get(delta_key, 0.0)

                    delta_dict["delta_elo"] = profile_a["elo"] - profile_b["elo"]
                    delta_dict["delta_win_streak"] = profile_a["win_streak"] - profile_b["win_streak"]
                    delta_dict["delta_loss_streak"] = profile_a["loss_streak"] - profile_b["loss_streak"]
                    delta_dict["delta_win_rate_last_5"] = profile_a["win_rate_5"] - profile_b["win_rate_5"]
                    delta_dict["delta_ufc_win_rate"] = profile_a["ufc_win_rate"] - profile_b["ufc_win_rate"]
                    delta_dict["delta_ufc_fights"] = profile_a["ufc_fights"] - profile_b["ufc_fights"]
                    delta_dict["delta_rank"] = profile_b["rank"] - profile_a["rank"]
                    delta_dict["is_ranked_f1"] = profile_a["is_ranked"]
                    delta_dict["is_ranked_f2"] = profile_b["is_ranked"]
                    delta_dict["delta_win_rate_3y"] = profile_a["wr_3y"] - profile_b["wr_3y"]
                    delta_dict["delta_SlpM_3y"] = (profile_a["slpm_3y"] - profile_b["slpm_3y"]) if (pd.notna(profile_a["slpm_3y"]) and pd.notna(profile_b["slpm_3y"])) else medians.get("delta_SlpM_3y", 0.0)
                    delta_dict["delta_SApM_3y"] = (profile_a["sapm_3y"] - profile_b["sapm_3y"]) if (pd.notna(profile_a["sapm_3y"]) and pd.notna(profile_b["sapm_3y"])) else medians.get("delta_SApM_3y", 0.0)
                    delta_dict["delta_TD_Def_3y"] = (profile_a["td_def_3y"] - profile_b["td_def_3y"]) if (pd.notna(profile_a["td_def_3y"]) and pd.notna(profile_b["td_def_3y"])) else medians.get("delta_TD_Def_3y", 0.0)

                    X_input = pd.DataFrame([delta_dict])[FEATURE_COLS_V3]
                    probs = model.predict_proba(X_input)[0]
                    prob_b_loss, prob_a_win = probs[0], probs[1]

                    pct_a = prob_a_win * 100.0
                    pct_b = prob_b_loss * 100.0

                    if not has_valid_odds:
                        signal_html = f'<div class="signal-pill-wait">{t["odds_pending"]}</div>'
                        html_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
<div style="display: flex; gap: 20px; margin-bottom: 16px;">
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔴 {f1_raw}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #94A3B8; margin: 4px 0 8px 0;">Odds: N/A</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔵 {f2_raw}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #94A3B8; margin: 4px 0 8px 0;">Odds: N/A</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>
{signal_html}
</div>"""
                        render_clean_html(html_card)
                        continue

                    ev_a = (prob_a_win * odds_a) - 1.0
                    ev_b = (prob_b_loss * odds_b) - 1.0
                    best_ev = max(ev_a, ev_b)
                    best_fighter = f1_raw if ev_a >= ev_b else f2_raw

                    if best_ev > 0.20:
                        signal_html = f'<div class="signal-pill-rec">{t["high_confidence"].format(fighter=best_fighter.upper())}</div>'
                    else:
                        signal_html = f'<div class="signal-pill-no">{t["insufficient_confidence"]}</div>'

                    html_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
<div style="display: flex; gap: 20px; margin-bottom: 16px;">
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔴 {f1_raw}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">Odds: {odds_a:.2f}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔵 {f2_raw}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">Odds: {odds_b:.2f}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>
{signal_html}
</div>"""
                    render_clean_html(html_card)

                except Exception as ex:
                    st.error(f"Render Error : {ex}")

    # =========================================================================
    # PAGE 3 : 📜 COMBATS ANTÉRIEURS
    # =========================================================================
    elif page == "past":
        st.markdown(f"### {t['past_title']}")

        tot_prof = fin_summary.get("total_profit", 0.0)
        tot_stake = fin_summary.get("total_staked", 0.0)
        roi_p = fin_summary.get("roi_pct", 0.0)
        win_r = fin_summary.get("win_rate_pct", 0.0)
        v_count = fin_summary.get("value_bets_count", 0)
        v_won = fin_summary.get("value_bets_won", 0)

        global_prof_color = "#10B981" if tot_prof >= 0 else "#EF4444"
        global_roi_color = "#10B981" if roi_p >= 0 else "#EF4444"

        html_summary_card = f"""<div class="summary-card-pure-white">
<div style="font-size: 0.85rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; text-align: center;">
    {t.get('global_summary_title', '🌐 Global Performance')}
</div>
<div style="display: flex; gap: 16px; text-align: center;">
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['net_profit']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {global_prof_color};">{tot_prof:+.2f} €</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['roi_yield']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{roi_p:.1f}%</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['win_rate']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{win_r:.1f}%</div>
<div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{v_won}/{v_count} {t['won_text']}</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['staked_vol']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{tot_stake:.0f} €</div>
<div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{v_count} {t['bets_text']}</div>
</div>
</div>
</div>"""
        render_clean_html(html_summary_card)

        if not past_cards:
            st.info("ℹ️ No past card archived.")
        else:
            past_keys = list(past_cards.keys())

            selected_past_key = st.selectbox(
                t["select_past_card"],
                past_keys,
                format_func=lambda k: f"📜 {k} ({len(deduplicate_card_fights(past_cards[k].get('fights', [])))} fights)",
                key="sb_past"
            )

            p_card_info = past_cards[selected_past_key]
            p_fights = deduplicate_card_fights(p_card_info.get("fights", []))

            # Calcul dynamique spécifique à la carte sélectionnée
            card_staked = 0.0
            card_profit = 0.0
            card_vb_count = 0
            card_vb_won = 0

            for fight in p_fights:
                res_status = fight.get("result_status")
                net_gain = fight.get("net_gain", 0.0)
                winner = fight.get("winner")
                pf1 = fight.get("f1", "")
                pf2 = fight.get("f2", "")

                is_f1_win = bool(winner and fuzzy_match_fighter_name(winner, [pf1], threshold=0.70))
                is_f2_win = bool(winner and fuzzy_match_fighter_name(winner, [pf2], threshold=0.70))
                is_void = (
                    res_status == "VOID" or
                    not winner or
                    str(winner).upper().strip() in ["N/A", "NONE", "DRAW/NC", "NC", "CANCELLED", "VOID", "DRAW"] or
                    (not is_f1_win and not is_f2_win)
                )

                if fight.get("is_value_bet") and not is_void:
                    card_staked += 10.0
                    card_vb_count += 1
                    if res_status == "WIN" or net_gain > 0:
                        card_vb_won += 1
                        card_profit += net_gain
                    elif res_status == "LOSS" or net_gain < 0:
                        card_profit += net_gain

            card_roi = (card_profit / card_staked * 100.0) if card_staked > 0 else 0.0
            card_win_rate = (card_vb_won / card_vb_count * 100.0) if card_vb_count > 0 else 0.0

            card_prof_color = "#10B981" if card_profit >= 0 else "#EF4444"
            card_roi_color = "#10B981" if card_roi >= 0 else "#EF4444"

            html_card_summary = f"""<div class="summary-card-pure-white" style="margin-top: 12px; margin-bottom: 24px;">
<div style="font-size: 0.85rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; text-align: center;">
    {t.get('card_summary_title', '📅 Event Performance')}
</div>
<div style="display: flex; gap: 16px; text-align: center;">
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['net_profit']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {card_prof_color};">{card_profit:+.2f} €</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['roi_yield']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_roi:.1f}%</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['win_rate']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_win_rate:.1f}%</div>
<div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{card_vb_won}/{card_vb_count} {t['won_text']}</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['staked_vol']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_staked:.0f} €</div>
<div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{card_vb_count} {t['bets_text']}</div>
</div>
</div>
</div>"""
            render_clean_html(html_card_summary)


            for idx, fight in enumerate(p_fights, 1):
                pf1 = fight.get("f1", "")
                pf2 = fight.get("f2", "")
                flabel = fight.get("fight_label", f"Fight #{idx}")
                winner = fight.get("winner")
                res_status = fight.get("result_status")
                net_gain = fight.get("net_gain", 0.0)
                is_vb = fight.get("is_value_bet", False)
                bet_f = fight.get("bet_fighter")
                b_odds = fight.get("bet_odds")
                pct_a = fight.get("pct_a")
                pct_b = fight.get("pct_b")

                has_full = fight.get("has_full_data", True)
                has_odds = fight.get("has_valid_odds", True)
                ev_a_val = fight.get("ev_a")
                ev_b_val = fight.get("ev_b")
                max_ev_val = fight.get("max_ev_pct")

                badge_html = ""
                if flabel == "MAIN EVENT":
                    badge_html = '<span class="pill-main-red">🔥 MAIN EVENT</span>'
                elif flabel == "CO-MAIN EVENT":
                    badge_html = '<span class="pill-comain-dark">⭐ CO-MAIN EVENT</span>'

                metrics_html = ""
                if pct_a is not None and pct_b is not None:
                    odds_a_str = f"Odds: {fight.get('odds_a', 0.0):.2f}" if fight.get('odds_a') else "Odds: N/A"
                    odds_b_str = f"Odds: {fight.get('odds_b', 0.0):.2f}" if fight.get('odds_b') else "Odds: N/A"
                    metrics_html = f"""<div style="display: flex; gap: 20px; margin-bottom: 16px;">
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔴 {pf1}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_a_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔵 {pf2}</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_b_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>"""

                is_f1_win = bool(winner and fuzzy_match_fighter_name(winner, [pf1], threshold=0.70))
                is_f2_win = bool(winner and fuzzy_match_fighter_name(winner, [pf2], threshold=0.70))
                is_void = (
                    res_status == "VOID" or
                    (winner and str(winner).upper().strip() in ["N/A", "NONE", "DRAW/NC", "NC", "CANCELLED", "VOID", "DRAW"]) or
                    (winner and not is_f1_win and not is_f2_win)
                )

                if res_status == "VOID" or is_void:
                    res_html = f'<div class="result-pill-nobet">{t["void_pill"]}</div>'
                elif is_vb and res_status == "WIN":
                    res_html = f'<div class="result-pill-win">{t["won_pill"].format(gain=f"{net_gain:.2f}", fighter=bet_f, odds=f"{b_odds:.2f}", winner=winner)}</div>'
                elif is_vb and res_status == "LOSS":
                    res_html = f'<div class="result-pill-loss">{t["lost_pill"].format(fighter=bet_f, odds=f"{b_odds:.2f}", winner=winner)}</div>'
                else:
                    if not has_full:
                        res_html = f'<div class="result-pill-nobet">{t["insufficient_data"]}<br><span style="font-size:0.82rem; color:#64748B;">Winner: <b>{winner or "N/A"}</b>.</span></div>'
                    elif not has_odds:
                        res_html = f'<div class="result-pill-nobet">{t["odds_pending"]}<br><span style="font-size:0.82rem; color:#64748B;">Winner: <b>{winner or "N/A"}</b>.</span></div>'
                    else:
                        if max_ev_val is None:
                            best_ev_f = max(ev_a_val, ev_b_val) if (ev_a_val is not None and ev_b_val is not None) else 0.0
                            max_ev_val = best_ev_f * 100.0
                        res_html = f'<div class="result-pill-nobet">{t["no_bet_eval"].format(ev=f"{max_ev_val:+.1f}")}<br><span style="font-size:0.82rem; color:#64748B;">{t["no_bet_desc"].format(winner=winner or "N/A")}</span></div>'

                html_past_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{pf1} vs {pf2}</h3>
{metrics_html}
{res_html}
</div>"""
                render_clean_html(html_past_card)

    # =========================================================================
    # PAGE 4 : ⚖️ MENTIONS LÉGALES & CONFIDENTIALITÉ (PAGE DÉDIÉE A PART)
    # =========================================================================
    elif page == "legal":
        if st.button(t["back_home"], key="btn_back_home_top"):
            st.session_state["current_page"] = "home"
            st.rerun()

        st.markdown(f"### {t['legal_page_title']}")

        render_clean_html(f"""
        <div class="legal-card-pure-white">
            <h4 style="color: #0F172A; margin-top: 0;">{t['legal_sec1_title']}</h4>
            <p>{t['legal_publisher']}</p>
            
            <h4 style="color: #0F172A; margin-top: 1.5rem;">{t['legal_sec2_title']}</h4>
            <p>{t['legal_hosting']}</p>
            
            <h4 style="color: #0F172A; margin-top: 1.5rem;">{t['legal_sec3_title']}</h4>
            <p>{t['legal_ip']}</p>
            
            <h4 style="color: #0F172A; margin-top: 1.5rem;">{t['legal_sec4_title']}</h4>
            <p>{t['legal_privacy']}</p>
            
            <h4 style="color: #0F172A; margin-top: 1.5rem;">{t['legal_sec5_title']}</h4>
            <p>{t['disclaimer_ai']}</p>
            
            <h4 style="color: #1E293B; margin-top: 1.5rem;">{t['legal_sec6_title']}</h4>
            <p>{t['disclaimer_gaming']}</p>
            
            <h4 style="color: #1E293B; margin-top: 1.5rem;">{t['legal_sec7_title']}</h4>
            <p>{t['disclaimer_trademark']}</p>
            
            <h4 style="color: #1E293B; margin-top: 1.5rem;">{t['legal_sec8_title']}</h4>
            <p>{t['legal_ads']}</p>
            
            <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 20px 0;">
            <p style="font-weight: 600; color: #3D3EEA;">{t['bug_contact']}</p>
        </div>
        """)

        if st.button(t["back_home"], key="btn_back_home_bottom"):
            st.session_state["current_page"] = "home"
            st.rerun()

    # =========================================================================
    # FOOTER COMMON (BOUTON MENTIONS LÉGALES TOUT EN BAS & FOOTER)
    # =========================================================================
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_f1, c_f2, c_f3 = st.columns([1, 2, 1])
    with c_f2:
        if st.button(t["nav_legal"], key="btn_footer_legal_link", use_container_width=True):
            st.session_state["current_page"] = "legal"
            st.rerun()

    render_clean_html(f"""
    <div class="footer-aura">
        {t['footer']}
    </div>
    """)


if __name__ == "__main__":
    main()