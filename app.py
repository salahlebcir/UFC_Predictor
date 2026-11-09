"""
UFC Vision — High-End MMA Analytics & Prediction Platform
Couche Frontend Découplée (Streamlit).
Consomme exclusivement la couche de service backend (src.services) en mode 100% passif.
ZÉRO calcul ML lourd, ZÉRO appel réseau sortant lors des sessions utilisateur.
Interface Pure White, responsive mobile (grille 2x2), alignement horizontal strict (.fighter-name-box).
"""

import os
import sys
import base64
from pathlib import Path
import streamlit as st

# Forcer l'encodage UTF-8 sous Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Inclusion robuste des chemins projet
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Importation exclusive de la couche de service backend (SOC stricte)
from src.services import (
    get_upcoming_cards,
    get_past_cards,
    get_financial_summary,
    get_odds_metadata,
    get_feature_importances,
    deduplicate_card_fights
)


# Helper pour récupérer l'image logo sous forme base64
def get_logo_data_url():
    logo_path = PROJECT_ROOT / "logo.jpg"
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as img_f:
                encoded = base64.b64encode(img_f.read()).decode("utf-8")
                return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            pass
    return "https://ufcvision.com/logo.jpg"


def get_logo_base64():
    return get_logo_data_url()


# Helper pour récupérer l'URL Open Graph avec Cache-Busting
def get_og_image_url():
    og_path = PROJECT_ROOT / "og-image.jpg"
    if og_path.exists():
        mtime = int(og_path.stat().st_mtime)
        return f"https://ufcvision.com/og-image.jpg?v={mtime}"
    return "https://ufcvision.com/og-image.jpg?v=2"


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
        "hero_description": "UFC Vision is an independent project by MMA data enthusiasts, not affiliated with the UFC. Our model analyzes over 20 statistical factors per matchup based on 10 years of fight history. <b>We are not responsible for your bets; we analyze data and compare it against bookmakers' odds.</b>",
        "stat_winrate_desc": "Bot Winrate (2015 - 2026)",
        "stat_roi_desc": "Bot ROI (2015 - 2026)",
        "upcoming_title": "🔮 Upcoming UFC Event Predictions",
        "select_upcoming_card": "Select an upcoming UFC card:",
        "insufficient_data": "🔘 INSUFFICIENT DATA — Incomplete UFC history.",
        "odds_pending": "⏳ ODDS PENDING — Awaiting official odds.",
        "no_odds_archived": "⚪ NO ODDS ARCHIVED — Historical odds missing.",
        "high_confidence": "🟢 VALUE OPPORTUNITY: {fighter}",
        "insufficient_confidence": "🚨 NO VALUE DETECTED",
        "global_summary_title": "🌐 Global Performance",
        "card_summary_title": "📅 Event Performance",
        "past_title": "📊 Real Performance (10€ Simulated Stake)",
        "net_profit": "💵 Total Net Profit",
        "volume_sub": "{staked:.0f}€ staked ({bets} bets)",
        "roi_yield": "📈 ROI Yield",
        "win_rate_value": "🎯 Opportunity Win Rate",
        "opportunity_info": "💡 <b>Note:</b> A <i>Value Opportunity</i> does <b>NOT necessarily mean the fighter is the favorite</b> to win. It indicates an Expected Value (EV) greater than +20% relative to market odds, which maximizes long-term ROI based on our historical backtests.",
        "accuracy_all": "🔮 Prediction Accuracy (All Fights)",
        "won_text": "gained",
        "correct_text": "correct",
        "bets_text": "bets",
        "won_pill": "🟢 WON (+{gain} €) — Successful bet on {fighter} (Odds: {odds}). Winner: {winner}.",
        "lost_pill": "🔴 LOST (-10.00 €) — Bet placed on {fighter} (Odds: {odds}). Winner: {winner}.",
        "no_bet_eval": "⚪ NO BET — No Value Bet (EV max: {ev}%)",
        "no_bet_desc": "Avoided bet: Insufficient value. Winner: {winner}.",
        "void_pill": "⚪ CANCELLED / VOID — Fight did not take place (Stake refunded)",
        "odds_freshness": "⚡ Odds updated {mins} mins ago from The Odds API",
        "odds_updated_mins": "⚡ Odds updated {mins} mins ago from The Odds API",
        "odds_updated_hours": "⚡ Odds updated {hours}h {mins}m ago from The Odds API",
        "bug_contact": "✉️ Found a bug or have a question? contact@auradev.fr",
        # FEATURE IMPORTANCE EN
        "feature_importance_title": "📊 Which factors are the most important in our AI model?",
        "feature_importance_desc": "Our predictive AI analyzes differential statistical variables per fight. Here is the exact weight of each factor in the model's decision-making process:",
        # FAQ EN
        "faq_title": "❓ Frequently Asked Questions (FAQ)",
        "q1": "How does UFC Vision's AI work?",
        "a1": "Our predictive AI algorithm evaluates over 20 differential statistical factors between two fighters (ELO score gaps, strike output, takedown defense rate, win streaks, recent rankings, etc.) built upon 10 years of historical UFC fight data.",
        "q2": "Where do fight data and odds come from?",
        "a2": "Fight statistics are extracted from official UFC fight archives, while market odds are fetched periodically through global bookmaker aggregator APIs in background mode.",
        "q3": "What is a Value Opportunity?",
        "a3": "A Value Opportunity indicates that the AI-calculated probability shows a significant statistical edge (Value > +20% EV) when matched against published market odds.",
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
        "legal_ip": "<b>Intellectual Property:</b> All Machine Learning models, algorithms, interface designs, and code powering UFC Vision are the exclusive intellectual property of Aura Dev. Automated data scraping or commercial reproduction is strictly prohibited.",
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
        "hero_description": "UFC Vision est un projet indépendant mené par des passionnés de data MMA, non affilié à l'UFC. Notre modèle analyse plus de 20 facteurs statistiques par affrontement sur 10 ans d'historique. <b>Nous ne sommes pas responsables de vos paris : nous analysons des données et les comparons à celles des bookmakers.</b>",
        "stat_winrate_desc": "Winrate du bot (2015 - 2026)",
        "stat_roi_desc": "ROI du bot (2015 - 2026)",
        "upcoming_title": "🔮 Prédictions des Prochains Événements UFC",
        "select_upcoming_card": "Sélectionnez une carte UFC à venir :",
        "insufficient_data": "🔘 DONNÉES INSUFFISANTES — Historique UFC incomplet.",
        "odds_pending": "⏳ COTES EN ATTENTE — En attente des cotes officielles.",
        "no_odds_archived": "⚪ COTES HISTORIQUES NON ARCHIVÉES — Cotes manquantes.",
        "high_confidence": "🟢 OPPORTUNITÉ DÉTECTÉE : {fighter}",
        "insufficient_confidence": "🚨 AUCUNE OPPORTUNITÉ INTÉRESSANTE",
        "global_summary_title": "🌐 Bilan Global",
        "card_summary_title": "📅 Bilan de cette soirée",
        "past_title": "📊 Performance Réelle (Mise Fictive 10 €)",
        "net_profit": "💵 Profit Net Total",
        "volume_sub": "{staked:.0f} € misés ({bets} paris)",
        "roi_yield": "📈 Rendement ROI",
        "win_rate_value": "🎯 Taux de Réussite (Opportunités)",
        "opportunity_info": "💡 <b>Note :</b> Une <i>Opportunité Détectée</i> ne signifie <b>PAS FORCÉMENT que le combattant est favori</b>. Cela indique une espérance mathématique supérieure à +20% au vu des cotes, ce qui permet de maximiser le ROI à long terme selon nos tests historiques.",
        "accuracy_all": "🔮 Précision Pronos (Tous Combats)",
        "select_past_card": "Sélectionnez un événement passé de l'UFC :",
        "won_text": "gagnés",
        "correct_text": "justes",
        "bets_text": "paris",
        "won_pill": "🟢 GAGNÉ (+{gain} €) — Pari réussi sur {fighter} (Cote : {odds}). Vainqueur : {winner}.",
        "lost_pill": "🔴 PERDU (-10.00 €) — Pari engagé sur {fighter} (Cote : {odds}). Vainqueur : {winner}.",
        "no_bet_eval": "⚪ NO BET — Pas de Value Bet (EV max : {ev}%)",
        "no_bet_desc": "Pari évité : Valeur insuffisante. Vainqueur : {winner}.",
        "void_pill": "⚪ ANNULÉ / VOID — Combat non disputé (Pari remboursé)",
        "odds_freshness": "⚡ Cotes actualisées il y a {mins} min via The Odds API",
        "odds_updated_mins": "⚡ Cotes mises à jour il y a {mins} min depuis The Odds API",
        "odds_updated_hours": "⚡ Cotes mises à jour il y a {hours}h {mins}min depuis The Odds API",
        "bug_contact": "✉️ Une question ou une erreur à signaler ? contact@auradev.fr",
        # FEATURE IMPORTANCE FR
        "feature_importance_title": "📊 Quels sont les facteurs les plus importants dans notre modèle IA ?",
        "feature_importance_desc": "Notre IA prédictive analyse des variables statistiques différentielles par affrontement. Voici le poids exact de chaque facteur dans la prise de décision du modèle :",
        # FAQ FR
        "faq_title": "❓ Foire Aux Questions (FAQ)",
        "q1": "Comment fonctionne l'intelligence artificielle d'UFC Vision ?",
        "a1": "Notre algorithme d'IA prédictive compare simultanément plus de 20 variables statistiques ajustées entre deux combattants (différentiels d'ELO, volume de coups, efficacité de défense de takedown, séries de victoires, classement récent, etc.) sur les 10 dernières années de combats UFC.",
        "q2": "D'où proviennent les données et les cotes ?",
        "a2": "Les métriques de combat sont issues de l'historique officiel de l'UFC, et les cotes sont actualisées régulièrement en arrière-plan via des APIs agrégatrices de bookmakers mondiaux.",
        "q3": "Qu'est-ce qu'une Opportunité Détectée (Value Bet) ?",
        "a3": "Une opportunité détectée indique que la probabilité calculée par l'IA présente un avantage statistique significatif (Value > +20% d'EV) par rapport à la cote proposée sur le marché.",
        "q4": "UFC Vision est-il affilié à l'UFC ?",
        "a4": "Non. UFC Vision est un projet d'analyse indépendant conçu par des passionnés de MMA. Il n'est en aucun cas affilié, sponsorisé ou approuvé par l'UFC ou TKO Group Holdings.",
        "faq_contact": "Vous avez d'autres questions ? N'hésitez pas à nous contacter à contact@auradev.fr",
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
        "legal_ip": "<b>Propriété Intellectuelle :</b> L'ensemble des modèles de Machine Learning, algorithmes, interfaces et code source sont la propriété exclusive d'Aura Dev. Toute aspiration automatisée de données (scraping) ou réutilisation commerciale est strictement interdite.",
        "legal_privacy": "<b>Données Personnelles & Cookies :</b> UFC Vision ne requiert la création d'aucun compte et ne collecte aucune donnée nominative directe. Des outils de mesure d'audience (Google Tag Manager, Google Analytics 4) et des régies publicitaires tierces (Google AdSense) utilisent des cookies pour analyser le trafic et diffuser des annonces pertinentes.",
        "legal_ads": "<b>Annonces Publicitaires :</b> Le site héberge des espaces publicitaires. Les régies partenaires traitent des données techniques d'affichage non identifiables pour adapter la pertinence des publicités.",
        "disclaimer_ai": "<b>Avertissement IA :</b> UFC Vision est un outil d'aide à la décision. Les prédictions sont fournies à titre purement informatif. Aucun gain n'est garanti et Aura Dev décline toute responsabilité en cas de pertes liées à l'utilisation du service.",
        "disclaimer_gaming": "<b>Jeu Responsable (+18) :</b> Les paris sportifs sont strictement interdits aux mineurs. Jouer comporte des risques : endettement, isolement, dépendance. Contactez Joueurs Info Service au 09 74 75 13 13.",
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
        "hero_description": "UFC Vision es un proyecto independiente creado por entusiastas de los datos de MMA, no afiliado a la UFC. Nuestro modelo analiza más de 20 factores estadísticos por combate en 10 años de historial. <b>No somos responsables de sus apuestas; analizamos datos y los comparamos con las casas de apuestas.</b>",
        "stat_winrate_desc": "Tasa de victoria del bot (2015 - 2026)",
        "stat_roi_desc": "ROI del bot (2015 - 2026)",
        "upcoming_title": "🔮 Predicciones de Próximos Eventos UFC",
        "select_upcoming_card": "Seleccione una cartelera de la UFC:",
        "insufficient_data": "🔘 DATOS INSUFFICIENTES — Historial de UFC incompleto.",
        "odds_pending": "⏳ CUOTAS PENDIENTES — Esperando cuotas oficiales.",
        "no_odds_archived": "⚪ SIN CUOTAS ARCHIVADAS — Cuotas históricas no disponibles.",
        "high_confidence": "🟢 OPORTUNIDAD DETECTADA: {fighter}",
        "insufficient_confidence": "🚨 SIN OPORTUNIDAD DE VALOR",
        "global_summary_title": "🌐 Rendimiento Global",
        "card_summary_title": "📅 Rendimiento de esta velada",
        "past_title": "📊 Rendimiento Real (Apuesta Simulada 10 €)",
        "net_profit": "💵 Beneficio Neto Total",
        "volume_sub": "{staked:.0f} € apostados ({bets} apuestas)",
        "roi_yield": "📈 Rendimiento ROI",
        "win_rate_value": "🎯 Tasa de Acierto (Oportunidades)",
        "opportunity_info": "💡 <b>Nota:</b> Una <i>Oportunidad Detectada</i> <b>NO significa necesariamente que el peleador sea el favorito</b>. Indica una esperanza matemática superior al +20% respecto a las cuotas, lo que permite maximizar el ROI a largo plazo según nuestras pruebas históricas.",
        "accuracy_all": "🔮 Precisión Pronósticos (Todos)",
        "select_past_card": "Seleccione un evento pasado de UFC:",
        "won_text": "ganados",
        "correct_text": "aciertos",
        "bets_text": "apuestas",
        "won_pill": "🟢 GANADO (+{gain} €) — Apuesta con éxito en {fighter} (Cuota: {odds}). Ganador: {winner}.",
        "lost_pill": "🔴 PERDIDO (-10.00 €) — Apuesta realizada en {fighter} (Cuota: {odds}). Ganador: {winner}.",
        "no_bet_eval": "⚪ NO BET — Sin Value Bet (EV máx: {ev}%)",
        "no_bet_desc": "Apuesta evitada: Valor insuficiente. Ganador: {winner}.",
        "void_pill": "⚪ CANCELADO / VOID — Combate no disputado (Apuesta reembolsada)",
        "odds_freshness": "⚡ Cuotas actualizadas hace {mins} min via The Odds API",
        "odds_updated_mins": "⚡ Cuotas actualizadas hace {mins} min desde The Odds API",
        "odds_updated_hours": "⚡ Cuotas actualizadas hace {hours}h {mins}min desde The Odds API",
        "bug_contact": "✉️ ¿Tienes alguna duda o error que reportar? contact@auradev.fr",
        # FEATURE IMPORTANCE ES
        "feature_importance_title": "📊 ¿Cuáles son los factores más importantes en nuestro modelo IA?",
        "feature_importance_desc": "Nuestra IA predictiva analiza variables estadísticas diferenciales por combate. Aquí está el peso exacto de cada factor en la toma de decisiones del modelo:",
        # FAQ ES
        "faq_title": "❓ Preguntas Frecuentes (FAQ)",
        "q1": "¿Cómo funciona la IA de UFC Vision?",
        "a1": "Nuestro algoritmo de IA predictiva analiza más de 20 variables estadísticas comparativas entre dos peleadores (diferencial de ELO, golpes por minuto, defensa de derribos, racha de victorias, etc.) basándose en 10 años de datos de la UFC.",
        "q2": "¿De dónde proceden los datos y las cuotas?",
        "a2": "Las estadísticas se extraen de los archivos oficiales de la UFC y las cuotas se actualizan periódicamente en segundo plano mediante APIs agregadoras internacionales.",
        "q3": "¿Qué es una Oportunidad de Valor (Value Bet)?",
        "a3": "Una oportunidad detectada indica que la probabilidad calculada por la IA ofrece una ventaja estadística sustancial (Valor > +20% EV) respecto a la cuota publicada por el mercado.",
        "q4": "¿Está UFC Vision afiliado a la UFC?",
        "a4": "No. UFC Vision es un proyecto analítico independiente creado por aficionados a las MMA. No está afiliado, patrocinado ni respaldado de ningún modo por UFC o TKO Group Holdings.",
        "faq_contact": "¿Tienes más preguntas? Contáctanos en contact@auradev.fr",
        # JURIDIQUE ES
        "legal_page_title": "⚖️ Aviso Legal, Privacidad y Política de Cookies",
        "legal_sec1_title": "1. Titular del Sitio y Aviso Legal",
        "legal_sec2_title": "2. Infraestructura y Alojamiento Cloud",
        "legal_sec3_title": "3. Propiedad Intelectual",
        "legal_sec4_title": "4. Política de Privacidad y RGPD",
        "legal_sec5_title": "5. Descargo de Responsabilidad de IA",
        "legal_sec6_title": "6. Juego Responsable (+18)",
        "legal_sec7_title": "7. Independencia de Marca",
        "legal_sec8_title": "8. Redes Publicitarias",
        "legal_publisher": "<b>Titular:</b> UFC Vision (https://ufcvision.com) es propiedad de Aura Dev (SIRET: 10542993000016). Contacto: contact@auradev.fr",
        "legal_hosting": "<b>Alojamiento Cloud:</b> DigitalOcean LLC | 101 Avenue of the Americas, 10th Floor, New York, NY 10013, EE.UU.",
        "legal_ip": "<b>Propiedad Intelectual:</b> Todos los modelos de Inteligencia Artificial, algoritmos e interfaz pertenecen en exclusiva a Aura Dev. Queda prohibida su extracción automatizada o copia comercial.",
        "legal_privacy": "<b>Privacidad:</b> No recopilamos datos personales directos sin su consentimiento.",
        "legal_ads": "<b>Publicidad:</b> Esta plataforma utiliza redes publicitarias automatizadas para financiar su mantenimiento.",
        "disclaimer_ai": "<b>Descargo IA:</b> UFC Vision es una herramienta analítica orientada exclusivamente a fines informativos. No nos hacemos responsables de las decisiones de apuestas.",
        "disclaimer_gaming": "<b>Juego Responsable (+18):</b> Las apuestas deportivas están prohibidas para menores de edad. Juegue con responsabilidad.",
        "disclaimer_trademark": "<b>Independencia:</b> Proyecto independiente no oficial. Las marcas de la UFC son propiedad exclusiva de sus respectivos dueños.",
        # COOKIES ES
        "cookie_dialog_title": "🍪 Preferencias de Cookies",
        "cookie_title": "Gestión de Cookies y Privacidad",
        "cookie_desc": "UFC Vision utiliza cookies técnicas esenciales y de medición para optimizar la experiencia.",
        "cookie_accept": "Aceptar Todas",
        "cookie_decline": "Solo Esenciales",
        "footer": "UFC Vision © 2026 — Todos los derechos reservados | Publicado por Aura Dev (SIRET: 10542993000016)"
    }
}


def render_clean_html(html_str):
    """Supprime tous les espaces d'indentation superflus au début de chaque ligne HTML."""
    clean_lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)


# =========================================================================
# CONFIGURATION STREAMLIT & STYLES CSS DESIGN SYSTEM PURE WHITE
# =========================================================================

st.set_page_config(
    page_title="UFC Vision — MMA Analytics & Predictions",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    #MainMenu, footer, header, [data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }

    .main .block-container {
        max-width: 980px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        border-radius: 9999px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.03) !important;
    }

    div[data-testid="stBaseButton-secondary"] button {
        border-radius: 9999px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stBaseButton-secondary"] button:hover {
        border-color: #CBD5E1 !important;
        background-color: #F8FAFC !important;
        transform: translateY(-1px);
    }

    .hero-bubble-text {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 28px !important;
        padding: 2.2rem 2.4rem !important;
        text-align: center !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important;
        margin-bottom: 2rem !important;
    }

    .stat-pill {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 24px !important;
        padding: 1.6rem !important;
        text-align: center !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03) !important;
    }
    .stat-val-huge {
        font-size: 2.8rem;
        font-weight: 900;
        color: #0F172A;
        line-height: 1;
        margin-bottom: 8px;
    }
    .stat-desc-clean {
        font-size: 0.85rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .summary-card-pure-white {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03);
    }

    .fight-card-pure-white {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02);
    }

    .legal-card-pure-white {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 24px;
        padding: 32px;
        margin: 20px 0;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03);
        line-height: 1.7;
        color: #334155;
    }

    .signal-pill-rec {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
        border-radius: 9999px;
        padding: 10px 18px;
        font-size: 0.95rem;
        font-weight: 800;
        text-align: center;
        margin-top: 14px;
    }
    .signal-pill-no {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        color: #991B1B;
        border-radius: 9999px;
        padding: 10px 18px;
        font-size: 0.9rem;
        font-weight: 800;
        text-align: center;
        margin-top: 14px;
    }
    .signal-pill-wait {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        color: #92400E;
        border-radius: 9999px;
        padding: 10px 18px;
        font-size: 0.9rem;
        font-weight: 800;
        text-align: center;
        margin-top: 14px;
    }
    .signal-pill-none {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #64748B;
        border-radius: 9999px;
        padding: 10px 18px;
        font-size: 0.9rem;
        font-weight: 800;
        text-align: center;
        margin-top: 14px;
    }

    .result-pill-win {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
        border-radius: 12px;
        padding: 10px 16px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-top: 12px;
    }
    .result-pill-loss {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        color: #991B1B;
        border-radius: 12px;
        padding: 10px 16px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-top: 12px;
    }
    .result-pill-nobet {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #64748B;
        border-radius: 12px;
        padding: 10px 16px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 12px;
    }

    .pill-main-red {
        background-color: #FEF2F2;
        border: 1px solid #FCA5A5;
        color: #DC2626;
        border-radius: 9999px;
        padding: 4px 12px;
        font-size: 0.75rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 8px;
    }
    .pill-comain-dark {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        color: #0F172A;
        border-radius: 9999px;
        padding: 4px 12px;
        font-size: 0.75rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 8px;
    }

    details.aura-accordion {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.02);
    }
    details.aura-accordion summary {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        cursor: pointer;
    }

    .footer-aura {
        text-align: center;
        padding: 2rem 0 2.5rem 0;
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* CONTENEUR FIXE DE NOM POUR ALIGNEMENT PARFAIT DES BARRES DE POURCENTAGE */
    .fighter-name-box {
        min-height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 8px;
    }

    /* GRILLE RESPONSIVE MOBILE POUR LES PANNEAUX DE PERFORMANCE (BILAN GLOBAL & BILAN SOIRÉE) */
    .perf-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        text-align: center;
    }
    @media (max-width: 640px) {
        .perf-stats-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 16px 8px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# POP-UP DIALOG COOKIES NATIVE STREAMLIT
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
# APPLICATION PRINCIPALE (FRONTEND PUR)
# =========================================================================

def main():
    # 🌐 SÉLECTEUR DE LANGUE ISOLÉ (Drapeaux discrets en haut à droite)
    lang_map = {"🇬🇧": "EN", "🇫🇷": "FR", "🇪🇸": "ES"}
    reverse_lang_map = {"EN": "🇬🇧", "FR": "🇫🇷", "ES": "🇪🇸"}

    if "lang" in st.query_params and st.query_params["lang"] in ["EN", "FR", "ES"]:
        st.session_state["lang"] = st.query_params["lang"]

    current_lang = st.session_state.get("lang", "EN")
    default_flag = reverse_lang_map.get(current_lang, "🇬🇧")

    selected_flag = st.selectbox(
        "lang_select_hidden",
        options=["🇬🇧", "🇫🇷", "🇪🇸"],
        index=["🇬🇧", "🇫🇷", "🇪🇸"].index(default_flag),
        label_visibility="collapsed",
        key="sb_language_flags"
    )

    new_lang = lang_map[selected_flag]
    if st.session_state.get("lang") != new_lang:
        st.session_state["lang"] = new_lang
        st.query_params["lang"] = new_lang
        st.rerun()

    current_lang = st.session_state["lang"]
    t = LANG_DATA.get(current_lang, LANG_DATA["EN"])

    # Session State Router
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "home"

    # 📜 SCRIPT DE SCROLL TO TOP AUTOMATIQUE
    st.components.v1.html(
        """
        <script>
            try {
                window.parent.scrollTo({top: 0, behavior: 'instant'});
            } catch(e) {}
        </script>
        """,
        height=0,
        width=0
    )

    # 🖼️ INJECTION DES BALISES META OPEN GRAPH DYNAMIQUES
    og_img_url = get_og_image_url()
    st.components.v1.html(f"""
    <script>
    try {{
        const doc = window.parent.document;
        const metaTags = [
            {{ property: 'og:title', content: 'UFC Vision — MMA Analytics & Predictions' }},
            {{ property: 'og:description', content: 'Premier UFC Prediction Bot powered by AI.' }},
            {{ property: 'og:image', content: '{og_img_url}' }},
            {{ property: 'og:url', content: 'https://ufcvision.com' }},
            {{ property: 'og:type', content: 'website' }},
            {{ name: 'twitter:card', content: 'summary_large_image' }},
            {{ name: 'twitter:title', content: 'UFC Vision — MMA Analytics & Predictions' }},
            {{ name: 'twitter:description', content: 'Premier UFC Prediction Bot powered by AI.' }},
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
        try:
            st.query_params.pop("cookie_consent", None)
        except Exception:
            pass

    # Script JS synchrone pour persistance localStorage (Langue + Cookies) & Nettoyage URL
    st.components.v1.html(f"""
    <script>
    try {{
        const parentWin = window.parent;
        const urlParams = new URLSearchParams(parentWin.location.search);

        // 1. Sauvegarde & Nettoyage Cookie Consent dans l'URL
        const consent = urlParams.get('cookie_consent');
        if (consent) {{
            parentWin.localStorage.setItem('ufc_cookie_consent', consent);
            urlParams.delete('cookie_consent');
            const cleanSearch = urlParams.toString() ? ('?' + urlParams.toString()) : '';
            const cleanUrl = parentWin.location.pathname + cleanSearch + parentWin.location.hash;
            parentWin.history.replaceState({{}}, parentWin.document.title, cleanUrl);
        }} else {{
            const savedConsent = parentWin.localStorage.getItem('ufc_cookie_consent');
            if (savedConsent && !urlParams.has('cookie_consent')) {{
                const url = new URL(parentWin.location.href);
                url.searchParams.set("cookie_consent", savedConsent);
                parentWin.location.replace(url.toString());
            }}
        }}

        // 2. Persistance de la Langue au Rafraîchissement (F5)
        let currentLang = '{current_lang}';
        if (currentLang) {{
            parentWin.localStorage.setItem('ufc_lang', currentLang);
        }}
    }} catch(e) {{}}
    </script>
    """, height=0, width=0)

    # DÉCLENCHEMENT POP-UP DIALOG COOKIES NATIVE SI PAS ENCORE DE CONSENTEMENT
    if not st.session_state.get("cookie_consent") and "cookie_consent" not in st.query_params:
        show_cookie_dialog(t)

    # ⚡ CHARGEMENT PASSIF ULTRA-RAPIDE VIA LA COUCHE SERVICE (SÉPARATION FRONT / BACK PURE)
    upcoming_cards = get_upcoming_cards()
    past_cards = get_past_cards()
    fin_summary = get_financial_summary()
    odds_meta = get_odds_metadata()
    odds_age_mins = odds_meta.get("age_mins", 1)
    odds_age_hours = int(odds_meta.get("age_hours", 0))
    odds_remaining_mins = odds_age_mins % 60

    # 🏛️ BANDEAU DE NAVIGATION PARFAITEMENT CENTRÉ
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

    # Stylisation dynamique de la pilule active & intégration du logo dans le bouton Accueil
    current_page = st.session_state.get("current_page", "home")
    if current_page == "past":
        active_btn_key = "btn_nav_past"
    elif current_page == "upcoming":
        active_btn_key = "btn_nav_upcoming"
    else:
        active_btn_key = "btn_nav_home"

    logo_data_url = get_logo_base64()

    st.markdown(f"""
    <style>
        button[data-testid="stBaseButton-{active_btn_key}"] {{
            border-color: #3D3EEA !important;
            box-shadow: 0 4px 14px rgba(61, 62, 234, 0.18) !important;
            font-weight: 800 !important;
        }}

        div[data-testid="stKey-btn_nav_home"] button,
        .st-key-btn_nav_home button {{
            background-image: url("{logo_data_url}") !important;
            background-size: contain !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 9999px !important;
            height: 42px !important;
            min-height: 42px !important;
            padding: 6px 16px !important;
        }}

        div[data-testid="stKey-btn_nav_home"] button p,
        div[data-testid="stKey-btn_nav_home"] button span,
        div[data-testid="stKey-btn_nav_home"] button div,
        .st-key-btn_nav_home button p {{
            opacity: 0 !important;
            font-size: 0px !important;
            color: transparent !important;
            visibility: hidden !important;
            display: none !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    page = current_page

    # =========================================================================
    # PAGE 1 : 🏠 ACCUEIL
    # =========================================================================
    if page == "home":
        # Bulle 1 : Le logo
        render_clean_html(f"""
        <div style="background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 36px !important; overflow: hidden !important; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important; margin: 3.5rem auto 2rem auto !important; text-align: center !important;">
            <img src="{logo_data_url}" alt="UFC Vision Logo" style="width: 100%; height: auto; display: block; border-radius: 36px;">
        </div>
        """)

        # Bulle 2 : Le texte de présentation
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

        # 📊 ACCORDÉON DES FACTEURS IA LES PLUS IMPORTANTS
        feat_importances = get_feature_importances(current_lang)
        feat_items_list = []
        for rank, (col, label, pct) in enumerate(feat_importances, 1):
            feat_items_list.append(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0;">
                <span style="font-weight: 700; color: #0F172A; font-size: 0.9rem;">#{rank} {label}</span>
                <span style="font-weight: 800; color: #3D3EEA; font-size: 0.92rem;">{pct:.1f}%</span>
            </div>
            """)
        feature_items_html = "\n".join(feat_items_list)

        render_clean_html(f"""
        <div style="margin-top: 3.5rem;">
            <details class="aura-accordion" style="margin-bottom: 1.25rem;">
                <summary><b>{t['feature_importance_title']}</b></summary>
                <div style="padding-top: 14px;">
                    <p style="margin-bottom: 16px; color: #475569; font-size: 0.95rem; line-height: 1.6;">
                        {t['feature_importance_desc']}
                    </p>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        {feature_items_html}
                    </div>
                </div>
            </details>

            <details class="aura-accordion">
                <summary><b>{t['faq_title']}</b></summary>
                <div style="padding-top: 14px; display: flex; flex-direction: column; gap: 14px;">
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q1']}</div>
                        <div style="color: #475569; font-size: 0.95rem; line-height: 1.6;">{t['a1']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q2']}</div>
                        <div style="color: #475569; font-size: 0.95rem; line-height: 1.6;">{t['a2']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q3']}</div>
                        <div style="color: #475569; font-size: 0.95rem; line-height: 1.6;">{t['a3']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q4']}</div>
                        <div style="color: #475569; font-size: 0.95rem; line-height: 1.6;">{t['a4']}</div>
                    </div>
                    <div style="margin-top: 6px; font-weight: 600; color: #3D3EEA; font-size: 0.9rem;">
                        {t['faq_contact']}
                    </div>
                </div>
            </details>
        </div>
        """)

    # =========================================================================
    # PAGE 2 : 🔮 COMBATS FUTURS (PRONOSTICS PRÉ-CALCULÉS PAR LE BACKEND)
    # =========================================================================
    elif page == "upcoming":
        st.markdown(f"### {t['upcoming_title']}")

        # Horodatage dynamique
        if odds_age_hours >= 1:
            freshness_str = t["odds_updated_hours"].format(hours=odds_age_hours, mins=odds_remaining_mins)
        else:
            freshness_str = t["odds_updated_mins"].format(mins=odds_age_mins)

        render_clean_html(f"""
        <div style="text-align: right; margin-bottom: 12px; font-size: 0.8rem; font-weight: 600; color: #64748B;">
            {freshness_str}
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

                has_full_data = ev.get("has_full_data", False)
                has_valid_odds = ev.get("has_valid_odds", False)
                pct_a = ev.get("pct_a")
                pct_b = ev.get("pct_b")
                odds_a = ev.get("odds_a")
                odds_b = ev.get("odds_b")
                is_vb = ev.get("is_value_bet", False)
                bet_fighter = ev.get("bet_fighter")

                badge_html = ""
                if fight_label == "MAIN EVENT":
                    badge_html = '<span class="pill-main-red">🔥 MAIN EVENT</span>'
                elif fight_label == "CO-MAIN EVENT":
                    badge_html = '<span class="pill-comain-dark">⭐ CO-MAIN EVENT</span>'

                if not has_full_data or pct_a is None or pct_b is None:
                    signal_html = f'<div class="signal-pill-none">{t["insufficient_data"]}</div>'
                    html_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
{signal_html}
</div>"""
                    render_clean_html(html_card)
                    continue

                odds_a_str = f"Odds: {odds_a:.2f}" if (has_valid_odds and odds_a) else "Odds: N/A"
                odds_b_str = f"Odds: {odds_b:.2f}" if (has_valid_odds and odds_b) else "Odds: N/A"
                odds_color = "#10B981" if has_valid_odds else "#94A3B8"

                if not has_valid_odds:
                    signal_html = f'<div class="signal-pill-wait">{t["odds_pending"]}</div>'
                elif is_vb and bet_fighter:
                    signal_html = f'<div class="signal-pill-rec">{t["high_confidence"].format(fighter=bet_fighter.upper())}</div>'
                else:
                    signal_html = f'<div class="signal-pill-no">{t["insufficient_confidence"]}</div>'

                html_card = f"""<div class="fight-card-pure-white">
{badge_html}
<h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
<div style="display: flex; gap: 20px; margin-bottom: 16px;">
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.9rem; font-weight: 700; color: #64748B;">🔴 {f1_raw}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: {odds_color}; margin: 4px 0 8px 0;">{odds_a_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.9rem; font-weight: 700; color: #64748B;">🔵 {f2_raw}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: {odds_color}; margin: 4px 0 8px 0;">{odds_b_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>
{signal_html}
</div>"""
                render_clean_html(html_card)

    # =========================================================================
    # PAGE 3 : 📜 COMBATS ANTÉRIEURS (POINT-IN-TIME BACKTEST SANS LEAKAGE)
    # =========================================================================
    elif page == "past":
        st.markdown(f"### {t['past_title']}")

        tot_prof = fin_summary.get("total_profit", 0.0)
        tot_stake = fin_summary.get("total_staked", 0.0)
        roi_p = fin_summary.get("roi_pct", 0.0)
        win_r = fin_summary.get("win_rate_pct", 0.0)
        v_count = fin_summary.get("value_bets_count", 0)
        v_won = fin_summary.get("value_bets_won", 0)
        tot_correct = fin_summary.get("total_correct_predictions", 0)
        tot_valid = fin_summary.get("total_valid_fights", 0)
        overall_acc = fin_summary.get("overall_accuracy_pct", 0.0)

        global_prof_color = "#10B981" if tot_prof >= 0 else "#EF4444"
        global_roi_formatted = f"+{roi_p:.1f}%" if roi_p >= 0 else f"{roi_p:.1f}%"

        html_summary_card = f"""<div class="summary-card-pure-white">
<div style="font-size: 0.85rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; text-align: center;">
    {t.get('global_summary_title', '🌐 Global Performance')}
</div>
<div class="perf-stats-grid">
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['net_profit']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {global_prof_color};">{tot_prof:+.2f} €</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{t['volume_sub'].format(staked=tot_stake, bets=v_count)}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['roi_yield']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{global_roi_formatted}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['win_rate_value']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{win_r:.1f}%</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{v_won}/{v_count} {t['won_text']}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['accuracy_all']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{overall_acc:.1f}%</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{tot_correct}/{tot_valid} {t['correct_text']}</div>
</div>
</div>
</div>"""
        render_clean_html(html_summary_card)

        if not past_cards:
            st.info("ℹ️ No past card archived.")
        else:
            past_keys = list(past_cards.keys())

            selected_past_key = st.selectbox(
                t.get("select_past_card", "Select a past UFC event:"),
                past_keys,
                format_func=lambda k: f"📜 {k} ({len(deduplicate_card_fights(past_cards[k].get('fights', [])))} fights)",
                key="sb_past"
            )

            p_card_info = past_cards[selected_past_key]
            p_fights = deduplicate_card_fights(p_card_info.get("fights", []))

            # Métriques de performance pré-calculées par le backend (zéro math dans le frontend)
            perf = p_card_info.get("performance", {})
            card_staked = perf.get("staked", 0.0)
            card_profit = perf.get("profit", 0.0)
            card_roi_formatted = perf.get("roi_formatted", "+0.0%")
            card_win_rate = perf.get("win_rate_pct", 0.0)
            card_vb_count = perf.get("vb_count", 0)
            card_vb_won = perf.get("vb_won", 0)
            card_accuracy = perf.get("accuracy_pct", 0.0)
            card_correct_count = perf.get("correct_count", 0)
            card_total_valid_fights = perf.get("valid_fights", 0)
            card_prof_color = perf.get("prof_color", "#10B981")

            html_card_summary = f"""<div class="summary-card-pure-white" style="margin-top: 12px; margin-bottom: 24px;">
<div style="font-size: 0.85rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; text-align: center;">
    {t.get('card_summary_title', '📅 Event Performance')}
</div>
<div class="perf-stats-grid">
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['net_profit']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {card_prof_color};">{card_profit:+.2f} €</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{t['volume_sub'].format(staked=card_staked, bets=card_vb_count)}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['roi_yield']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_roi_formatted}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['win_rate_value']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_win_rate:.1f}%</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{card_vb_won}/{card_vb_count} {t['won_text']}</div>
</div>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">{t['accuracy_all']}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{card_accuracy:.1f}%</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; margin-top: 4px;">{card_correct_count}/{card_total_valid_fights} {t['correct_text']}</div>
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
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.9rem; font-weight: 700; color: #64748B;">🔴 {pf1}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_a_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.9rem; font-weight: 700; color: #64748B;">🔵 {pf2}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_b_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>"""

                is_void = fight.get("is_void", False)

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
                        res_html = f'<div class="result-pill-nobet">{t["no_odds_archived"]}<br><span style="font-size:0.82rem; color:#64748B;">Winner: <b>{winner or "N/A"}</b>.</span></div>'
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
    # PAGE 4 : ⚖️ MENTIONS LÉGALES & CONFIDENTIALITÉ
    # =========================================================================
    elif page == "legal":
        # Force le navigateur à remonter tout en haut dès l'affichage des mentions légales
        st.components.v1.html(
            """
            <script>
                try {
                    window.parent.scrollTo(0, 0);
                    window.parent.scrollTo({top: 0, behavior: 'instant'});
                } catch(e) {}
            </script>
            """,
            height=0,
            width=0
        )

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
