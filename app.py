"""
MMA Vision — High-End MMA Analytics & Prediction Platform
Couche Frontend Découplée Ultra-Moderne (Streamlit).
Consomme exclusivement la couche de service backend (src.services) en mode 100% passif.
ZÉRO calcul ML lourd, ZÉRO appel réseau sortant lors des sessions utilisateur.
Design System 2026 : Open Atmosphere, Glassmorphism, Micro-Animations Hover, Bento Grid, Typographie Apple/Linear.
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


# Helper pour récupérer l'image logo sous forme base64 (MMA Vision)
def get_logo_data_url():
    logo_path = PROJECT_ROOT / "mmavision.jpg"
    if not logo_path.exists():
        logo_path = PROJECT_ROOT / "logo.jpg"

    if logo_path.exists():
        try:
            with open(logo_path, "rb") as img_f:
                encoded = base64.b64encode(img_f.read()).decode("utf-8")
                return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            pass
    return "https://mmavision.com/mmavision.jpg"


def get_logo_base64():
    return get_logo_data_url()


# Helper pour récupérer l'URL Open Graph avec Cache-Busting
def get_og_image_url():
    og_path = PROJECT_ROOT / "mmavision.jpg"
    if not og_path.exists():
        og_path = PROJECT_ROOT / "og-image.jpg"

    if og_path.exists():
        mtime = int(og_path.stat().st_mtime)
        return f"https://mmavision.com/mmavision.jpg?v={mtime}"
    return "https://mmavision.com/mmavision.jpg?v=2"


# DICTIONNAIRE CENTRALISÉ DE TRADUCTIONS ET TEXTES JURIDIQUES / FAQ (EN / FR / ES)
LANG_DATA = {
    "EN": {
        "page_title": "MMA Vision — MMA Analytics & Predictions",
        "nav_past": "📜 Past Fights",
        "nav_home": "🥊 MMA Vision",
        "nav_upcoming": "🔮 Upcoming Fights",
        "nav_legal": "⚖️ Legal Notice & Privacy Policy",
        "back_home": "← Back to Home",
        "hero_subtitle": "The Premier MMA Prediction Bot",
        "hero_description": "MMA Vision is an independent project by MMA data enthusiasts, not affiliated with the UFC or any MMA promotion. Our model analyzes over 20 statistical factors per matchup based on 10 years of fight history. <b>We are not responsible for your bets; we analyze data and compare it against bookmakers' odds.</b>",
        "stat_winrate_desc": "Bot Winrate (2015 - 2026)",
        "stat_roi_desc": "Bot ROI (2015 - 2026)",
        "verified_badge": "Verified Track Record",
        "cumulative_edge": "Cumulative Yield",
        "upcoming_title": "🔮 Upcoming MMA Event Predictions",
        "select_upcoming_card": "Select an upcoming MMA event:",
        "odds_updated_hours": "🕒 Odds updated {hours}h {mins}m ago • Auto Sync 2h",
        "odds_updated_mins": "🕒 Odds updated {mins}m ago • Auto Sync 2h",
        "odds_pending": "⏳ Odds Pending • Awaiting Bookmaker Lines",
        "insufficient_data": "⚠️ Insufficient UFC Data for one or both fighters (Debutant protected)",
        "insufficient_confidence": "⚪ Insufficient confidence (Expected Value below threshold)",
        "high_confidence": "🎯 High confidence on {fighter} (Expected Value > +20%)",
        "past_title": "📜 Past Fights & Historical Track Record",
        "global_summary_title": "🌐 Global Historical Performance",
        "card_summary_title": "📅 Event Historical Performance",
        "select_past_card": "Select an archived MMA event:",
        "net_profit": "Net Profit",
        "roi_yield": "ROI / Yield",
        "win_rate_value": "Value Bet Win Rate",
        "accuracy_all": "Prediction Accuracy (All Fights)",
        "volume_sub": "Volume: {staked:.0f} € ({bets} bets placed)",
        "won_text": "won",
        "correct_text": "correct",
        "won_pill": "✅ WON: +{gain} € on {fighter} (Odds: {odds}) — Winner: {winner}",
        "lost_pill": "❌ LOST: -10.00 € on {fighter} (Odds: {odds}) — Winner: {winner}",
        "void_pill": "⚪ VOID: Fight Cancelled / No Contest (0.00 €)",
        "no_odds_archived": "⚪ NO BET: No archived odds available for this bout.",
        "no_bet_eval": "⚪ NO BET: Evaluated (Max EV {ev}%)",
        "no_bet_desc": "EV below +20% threshold. Official Winner: <b>{winner}</b>.",
        "feature_importance_title": "🧠 Which factors are the most important in our AI model?",
        "feature_importance_desc": "Our predictive AI analyzes differential statistical variables per fight. Here is the exact relative weight of each factor in the model's decision-making process:",
        "faq_title": "💬 Frequently Asked Questions (FAQ)",
        "q1": "How does MMA Vision predict fights?",
        "a1": "Our predictive AI algorithm evaluates over 20 differential statistical factors between two fighters (ELO score gaps, strike output, takedown defense rate, win streaks, recent rankings, etc.) built upon 10 years of historical UFC and MMA fight data.",
        "q2": "What is a 'Value Bet'?",
        "a2": "A Value Bet occurs when our AI's predicted probability of a fighter winning is significantly higher than the probability implied by bookmakers' odds. We only flag bets with an Expected Value (EV) strictly greater than +20.0%, ensuring long-term profitability.",
        "q3": "How often are odds and predictions updated?",
        "a3": "Odds are synchronized every 2 hours via official sports betting data providers. Predictions adapt dynamically as soon as official opening and closing lines are confirmed.",
        "q4": "Are predictions financial advice?",
        "a4": "No. MMA Vision is an analytical tool built for sports enthusiasts and researchers. Past performance is not indicative of future results. Never bet more than you can comfortably afford to lose.",
        "faq_contact": "Questions or inquiries? Contact us at: aura.dev.contact@gmail.com",
        "legal_page_title": "⚖️ Legal Notice & Privacy Policy",
        "legal_sec1_title": "1. Site Publisher",
        "legal_publisher": "<b>Website Name:</b> MMA Vision (mmavision.com)<br><b>Legal Status:</b> Micro-entrepreneur / Aura Dev<br><b>SIRET:</b> 10542993000016<br><b>Headquarters:</b> Paris, France<br><b>Email:</b> aura.dev.contact@gmail.com",
        "legal_sec2_title": "2. Web Hosting",
        "legal_hosting": "<b>Host:</b> Hostinger International Ltd.<br><b>Address:</b> 61 Lordou Vironos Street, 6023 Larnaca, Cyprus<br><b>Website:</b> https://www.hostinger.com",
        "legal_sec3_title": "3. Intellectual Property",
        "legal_ip": "<b>Intellectual Property:</b> All Machine Learning models, algorithms, interface designs, and code powering MMA Vision are the exclusive intellectual property of Aura Dev. Automated data scraping or commercial reproduction is strictly prohibited.",
        "legal_sec4_title": "4. Privacy & Personal Data (GDPR)",
        "legal_privacy": "MMA Vision does not require user registration or personal account creation. We do not collect or sell personal identifying information. Anonymous usage telemetry and Google Analytics may be used strictly for performance optimization and technical stability.",
        "legal_sec5_title": "5. AI & Statistical Disclaimer",
        "disclaimer_ai": "<b>AI Disclaimer:</b> MMA Vision is an analytical decision-support tool. Predictions are strictly for informational purposes and do not constitute financial advice or sports betting recommendations. No outcome is guaranteed, and Aura Dev disclaims all liability for losses incurred.",
        "legal_sec6_title": "6. Responsible Gambling Notice",
        "disclaimer_gaming": "<b>Responsible Gambling:</b> Sports betting involves financial risks and potential addiction. Gambling is strictly restricted to individuals of legal age (18+ in most jurisdictions). If you or someone you know is struggling with gambling addiction, please seek support from dedicated helpline organizations.",
        "legal_sec7_title": "7. Non-Affiliation Trademark Disclaimer",
        "disclaimer_trademark": "<b>Trademark Disclaimer:</b> UFC, Ultimate Fighting Championship, and related marks are registered trademarks of Zuffa, LLC. MMA Vision is an independent analytics project and is not affiliated, endorsed, or associated with the UFC, Zuffa, LLC, or any MMA organization.",
        "legal_sec8_title": "8. Advertising Disclosure",
        "legal_ads": "MMA Vision may display commercial sponsorships or contextual affiliate banners. All external advertising links are clearly demarcated in compliance with digital consumer transparency standards.",
        "bug_contact": "Bug reports or legal inquiries: aura.dev.contact@gmail.com",
        "cookie_dialog_title": "🍪 Cookie Preferences",
        "cookie_title": "Cookie Management & Privacy",
        "cookie_desc": "MMA Vision uses essential technical cookies and anonymous analytics to ensure website stability and optimize performance.",
        "cookie_accept": "Accept All",
        "cookie_decline": "Essentials Only",
        "footer": "MMA Vision © 2026 — All Rights Reserved | Published by Aura Dev (SIRET: 10542993000016)"
    },
    "FR": {
        "page_title": "MMA Vision — Pronostics & Analytics MMA",
        "nav_past": "📜 Combats Passés",
        "nav_home": "🥊 MMA Vision",
        "nav_upcoming": "🔮 Combats Futurs",
        "nav_legal": "⚖️ Mentions Légales & Confidentialité",
        "back_home": "← Retour à l'Accueil",
        "hero_subtitle": "Le Meilleur Bot de Pronostics MMA",
        "hero_description": "MMA Vision est un projet indépendant créé par des passionnés de données MMA, non affilié à l'UFC ni à aucune organisation de MMA. Notre modèle analyse plus de 20 facteurs statistiques par combat sur 10 ans d'historique. <b>Nous ne sommes pas responsables de vos paris ; nous analysons les données et les comparons aux cotes des bookmakers.</b>",
        "stat_winrate_desc": "Taux de Victoire du Bot (2015 - 2026)",
        "stat_roi_desc": "ROI du Bot (2015 - 2026)",
        "verified_badge": "Historique Certifié",
        "cumulative_edge": "Rendement Cumulé",
        "upcoming_title": "🔮 Pronostics des Prochains Événements MMA",
        "select_upcoming_card": "Sélectionnez un événement MMA à venir :",
        "odds_updated_hours": "🕒 Cotes actualisées il y a {hours}h {mins}m • Sync Auto 2h",
        "odds_updated_mins": "🕒 Cotes actualisées il y a {mins}m • Sync Auto 2h",
        "odds_pending": "⏳ Cotes en Attente • En attente des lignes bookmakers",
        "insufficient_data": "⚠️ Données UFC insuffisantes pour l'un des combattants (Débutant protégé)",
        "insufficient_confidence": "⚪ Confiance insuffisante (Espérance mathématique sous le seuil)",
        "high_confidence": "🎯 Forte confiance sur {fighter} (Espérance mathématique > +20%)",
        "past_title": "📜 Combats Passés & Historique des Performances",
        "global_summary_title": "🌐 Bilan Historique Global",
        "card_summary_title": "📅 Bilan Historique de la Soirée",
        "select_past_card": "Sélectionnez une soirée MMA passée :",
        "net_profit": "Bénéfice Net",
        "roi_yield": "Rendement (ROI)",
        "win_rate_value": "Taux de Victoire Value Bets",
        "accuracy_all": "Précision Globale (Tous Combats)",
        "volume_sub": "Volume : {staked:.0f} € ({bets} paris engagés)",
        "won_text": "gagnés",
        "correct_text": "corrects",
        "won_pill": "✅ GAGNÉ : +{gain} € sur {fighter} (Cote : {odds}) — Vainqueur : {winner}",
        "lost_pill": "❌ PERDU : -10.00 € sur {fighter} (Cote : {odds}) — Vainqueur : {winner}",
        "void_pill": "⚪ ANNULÉ : Combat Annulé / No Contest (0.00 €)",
        "no_odds_archived": "⚪ PAS DE PARI : Aucune cote archivée disponible pour ce combat.",
        "no_bet_eval": "⚪ PAS DE PARI : Évalué (EV max {ev}%)",
        "no_bet_desc": "Espérance mathématique inférieure au seuil de +20%. Vainqueur officiel : <b>{winner}</b>.",
        "feature_importance_title": "🧠 Quels facteurs sont les plus importants dans notre modèle IA ?",
        "feature_importance_desc": "Notre Intelligence Artificielle analyse des variables statistiques différentielles par combat. Voici le poids exact de chaque facteur dans la prise de décision du modèle :",
        "faq_title": "💬 Foire Aux Questions (FAQ)",
        "q1": "Comment MMA Vision calcule-t-il ses pronostics ?",
        "a1": "Notre algorithme d'IA prédictive évalue plus de 20 facteurs statistiques différentiels entre les deux combattants (différentiel de score ELO, volume de frappe, défense de takedown, séries de victoires, classement récent, etc.) entraînés sur 10 ans d'historique UFC et MMA.",
        "q2": "Qu'est-ce qu'un 'Value Bet' ?",
        "a2": "Un Value Bet survient lorsque la probabilité calculée par notre IA est significativement plus élevée que la probabilité implicite de la cote proposée par le bookmaker. Nous ne retenons que les paris avec une espérance mathématique strictement supérieure à +20.0%.",
        "q3": "À quelle fréquence les cotes et données sont-elles mises à jour ?",
        "a3": "Les cotes sont synchronisées toutes les 2 heures via les fournisseurs officiels de données sportives. Les pronostics s'adaptent dynamiquement dès publication des cotes d'ouverture et de fermeture.",
        "q4": "Les prédictions constituent-elles un conseil financier ?",
        "a4": "Non. MMA Vision est un outil d'aide à la décision à vocation purement analytique et statistique. Les performances passées ne préjugent pas des résultats futurs. Ne pariez jamais plus que ce que vous pouvez vous permettre de perdre.",
        "faq_contact": "Questions ou partenariats ? Écrivez-nous à : aura.dev.contact@gmail.com",
        "legal_page_title": "⚖️ Mentions Légales & Politique de Confidentialité",
        "legal_sec1_title": "1. Éditeur du Site",
        "legal_publisher": "<b>Nom du site :</b> MMA Vision (mmavision.com)<br><b>Statut :</b> Micro-entrepreneur / Aura Dev<br><b>SIRET :</b> 10542993000016<br><b>Siège social :</b> Paris, France<br><b>Email :</b> aura.dev.contact@gmail.com",
        "legal_sec2_title": "2. Hébergement",
        "legal_hosting": "<b>Hébergeur :</b> Hostinger International Ltd.<br><b>Adresse :</b> 61 Lordou Vironos Street, 6023 Larnaca, Chypre<br><b>Site Web :</b> https://www.hostinger.fr",
        "legal_sec3_title": "3. Propriété Intellectuelle",
        "legal_ip": "<b>Propriété Intellectuelle :</b> L'ensemble des modèles de Machine Learning, algorithmes, interfaces graphiques et code source sont la propriété exclusive d'Aura Dev. Toute reproduction ou extraction automatisée est strictement interdite.",
        "legal_sec4_title": "4. Données Personnelles & RGPD",
        "legal_privacy": "MMA Vision ne propose aucun compte utilisateur et ne collecte aucune donnée personnelle nominative. Seuls des cookies techniques et des traceurs de mesure d'audience anonymes peuvent être utilisés pour assurer la stabilité et les performances.",
        "legal_sec5_title": "5. Avertissement IA & Données Statistiques",
        "disclaimer_ai": "<b>Avertissement IA :</b> MMA Vision est un outil d'analyse décisionnelle. Les pronostics n'ont aucune valeur de certitude et ne constituent en aucun cas des conseils en investissement financier ou en paris sportifs.",
        "legal_sec6_title": "6. Prévention des Jeux d'Argent & Addiction",
        "disclaimer_gaming": "<b>Jeu Responsable :</b> Les paris sportifs comportent des risques d'endettement et d'addiction. Interdit aux mineurs (-18 ans). En cas de difficulté, contactez Joueurs Info Service au 09 74 75 13 13 (appel non surtaxé).",
        "legal_sec7_title": "7. Avertissement de Marque & Non-Affiliation",
        "disclaimer_trademark": "<b>Marques :</b> UFC, Ultimate Fighting Championship et les noms associés sont des marques déposées de Zuffa, LLC. MMA Vision est un outil d'analyse indépendant et n'est affilié, sponsorisé ni approuvé par l'UFC, Zuffa, LLC ou toute autre ligue de MMA.",
        "legal_sec8_title": "8. Transparence Publicitaire",
        "legal_ads": "MMA Vision peut afficher des partenariats commerciaux ou des liens d'affiliation avec des bookmakers légaux. Ces mentions sont toujours clairement identifiées conformément aux exigences légales.",
        "bug_contact": "Signalement de bug ou contact juridique : aura.dev.contact@gmail.com",
        "cookie_dialog_title": "🍪 Préférences Cookies",
        "cookie_title": "Gestion des Cookies et de la Confidentialité",
        "cookie_desc": "MMA Vision utilise des cookies techniques indispensables et des outils d'analyse anonymes pour garantir la fluidité de navigation et le suivi des performances.",
        "cookie_accept": "Tout Accepter",
        "cookie_decline": "Essentiels Uniquement",
        "footer": "MMA Vision © 2026 — Tous droits réservés | Édité par Aura Dev (SIRET : 10542993000016)"
    },
    "ES": {
        "page_title": "MMA Vision — Pronósticos y Analítica MMA",
        "nav_past": "📜 Peleas Pasadas",
        "nav_home": "🥊 MMA Vision",
        "nav_upcoming": "🔮 Próximas Peleas",
        "nav_legal": "⚖️ Aviso Legal y Privacidad",
        "back_home": "← Volver al Inicio",
        "hero_subtitle": "El Mejor Bot de Pronósticos de MMA",
        "hero_description": "MMA Vision es un proyecto independiente creado por entusiastas de los datos de MMA, no afiliado a la UFC ni a ninguna promoción de MMA. Nuestro modelo analiza más de 20 factores estadísticos por combate en 10 años de historial. <b>No somos responsables de sus apuestas; analizamos datos y los comparamos con las casas de apuestas.</b>",
        "stat_winrate_desc": "Tasa de Acierto del Bot (2015 - 2026)",
        "stat_roi_desc": "ROI del Bot (2015 - 2026)",
        "verified_badge": "Historial Verificado",
        "cumulative_edge": "Rendimiento Acumulado",
        "upcoming_title": "🔮 Pronósticos de Próximos Eventos MMA",
        "select_upcoming_card": "Selecciona un evento MMA próximo:",
        "odds_updated_hours": "🕒 Cuotas actualizadas hace {hours}h {mins}m • Sync Auto 2h",
        "odds_updated_mins": "🕒 Cuotas actualizadas hace {mins}m • Sync Auto 2h",
        "odds_pending": "⏳ Cuotas Pendientes • Esperando líneas de apertura",
        "insufficient_data": "⚠️ Datos insuficientes en UFC para uno de los peleadores (Debutante protegido)",
        "insufficient_confidence": "⚪ Confianza insuficiente (Valor Esperado por debajo del umbral)",
        "high_confidence": "🎯 Alta confianza en {fighter} (Valor Esperado > +20%)",
        "past_title": "📜 Peleas Pasadas e Historial de Resultados",
        "global_summary_title": "🌐 Balance Histórico Global",
        "card_summary_title": "📅 Balance Histórico de la Velada",
        "select_past_card": "Selecciona una velada MMA archivada:",
        "net_profit": "Beneficio Neto",
        "roi_yield": "Rendimiento (ROI)",
        "win_rate_value": "Tasa de Victoria en Value Bets",
        "accuracy_all": "Precisión Global (Todas las Peleas)",
        "volume_sub": "Volumen: {staked:.0f} € ({bets} apuestas realizadas)",
        "won_text": "ganadas",
        "correct_text": "correctas",
        "won_pill": "✅ GANADA: +{gain} € por {fighter} (Cuota: {odds}) — Ganador: {winner}",
        "lost_pill": "❌ PERDIDA: -10.00 € por {fighter} (Cuota: {odds}) — Ganador: {winner}",
        "void_pill": "⚪ NULA: Pelea Cancelada / Sin Resultado (0.00 €)",
        "no_odds_archived": "⚪ SIN APUESTA: Sin cuotas archivadas para esta pelea.",
        "no_bet_eval": "⚪ SIN APUESTA: Evaluada (EV máx {ev}%)",
        "no_bet_desc": "Valor esperado inferior al umbral de +20%. Ganador oficial: <b>{winner}</b>.",
        "feature_importance_title": "🧠 ¿Cuáles son los factores más importantes en nuestro modelo IA?",
        "feature_importance_desc": "Nuestra IA predictiva analiza variables estadísticas diferenciales por combate. Aquí está el peso exacto de cada factor en la toma de decisiones del modelo:",
        "faq_title": "💬 Preguntas Frecuentes (FAQ)",
        "q1": "¿Cómo predice MMA Vision los combates?",
        "a1": "Nuestro algoritmo de IA predictiva analiza más de 20 variables estadísticas comparativas entre dos peleadores (diferencial de ELO, golpes por minuto, defensa de derribos, racha de victorias, etc.) basándose en 10 años de datos de la UFC y MMA.",
        "q2": "¿Qué es una 'Value Bet'?",
        "a2": "Una Value Bet ocurre cuando la probabilidad calculada por nuestra IA es significativement mayor que la probabilidad implícita de la cuota del bookmaker. Solo seleccionamos apuestas con una ventaja matemática superior a +20.0%.",
        "q3": "¿Con qué frecuencia se actualizan las cuotas?",
        "a3": "Las cuotas se actualizan automáticamente cada 2 horas a través de proveedores oficiales de datos. Los pronósticos se ajustan dinámicamente con las cuotas oficiales de cierre.",
        "q4": "¿Son estos pronósticos asesoramiento financiero?",
        "a4": "No. MMA Vision es una herramienta estadística analítica para aficionados. Los resultados pasados no garantizan beneficios futuros. Nunca apueste dinero que no pueda permitirse perder.",
        "faq_contact": "¿Dudas o consultas? Contáctenos en: aura.dev.contact@gmail.com",
        "legal_page_title": "⚖️ Aviso Legal y Política de Privacidad",
        "legal_sec1_title": "1. Titular del Sitio Web",
        "legal_publisher": "<b>Sitio Web:</b> MMA Vision (mmavision.com)<br><b>Titular:</b> Microempresa / Aura Dev<br><b>SIRET:</b> 10542993000016<br><b>Sede:</b> París, Francia<br><b>Email:</b> aura.dev.contact@gmail.com",
        "legal_sec2_title": "2. Alojamiento Web",
        "legal_hosting": "<b>Proveedor:</b> Hostinger International Ltd.<br><b>Dirección:</b> 61 Lordou Vironos Street, 6023 Larnaca, Chipre<br><b>Web:</b> https://www.hostinger.es",
        "legal_sec3_title": "3. Propiedad Intelectual",
        "legal_ip": "<b>Propiedad Intelectual:</b> Todos los modelos de Inteligencia Artificial, algoritmos e interfaz pertenecen en exclusiva a Aura Dev. Queda prohibida su extracción automatizada o copia comercial.",
        "legal_sec4_title": "4. Privacidad y Protección de Datos (RGPD)",
        "legal_privacy": "MMA Vision no requiere registro de usuario ni almacena datos personales identificables. Se emplean cookies técnicas y de analítica anónima para garantizar la funcionalidad y optimizar el rendimiento.",
        "legal_sec5_title": "5. Exención de Responsabilidad IA",
        "disclaimer_ai": "<b>Aviso IA:</b> MMA Vision es una herramienta de apoyo analítico. Las predicciones son meramente informativas y no constituyen asesoramiento financiero ni recomendaciones de apuestas.",
        "legal_sec6_title": "6. Juego Responsable",
        "disclaimer_gaming": "<b>Juego Responsable:</b> Las apuestas deportivas conllevan riesgo económico y adicción. Prohibido a menores de 18 años. Si necesita asistencia, consulte con organizaciones especializadas.",
        "legal_sec7_title": "7. Descargo de Marcas",
        "disclaimer_trademark": "<b>Marcas Registradas:</b> UFC y marcas derivadas son propiedad de Zuffa, LLC. MMA Vision es un proyecto analítico independiente sin relación comercial con Zuffa, LLC ni UFC.",
        "legal_sec8_title": "8. Transparencia Publicitaria",
        "legal_ads": "MMA Vision puede incluir enlaces de patrocinio o afiliación con operadores regulados, siempre identificados de acuerdo con la normativa publicitaria.",
        "bug_contact": "Aviso de errores o consultas legales: aura.dev.contact@gmail.com",
        "cookie_dialog_title": "🍪 Preferencias de Cookies",
        "cookie_title": "Gestión de Cookies y Privacidad",
        "cookie_desc": "MMA Vision utiliza cookies técnicas esenciales y de medición para optimizar la experiencia.",
        "cookie_accept": "Aceptar Todas",
        "cookie_decline": "Solo Esenciales",
        "footer": "MMA Vision © 2026 — Todos los derechos reservados | Publicado por Aura Dev (SIRET: 10542993000016)"
    }
}


def render_clean_html(html_str):
    """Supprime tous les espaces d'indentation superflus au début de chaque ligne HTML."""
    clean_lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)


# =========================================================================
# CONFIGURATION STREAMLIT & DESIGN SYSTEM ULTRA-MODERNE 2026 (OPEN BENTO)
# =========================================================================

st.set_page_config(
    page_title="MMA Vision — MMA Analytics & Predictions",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    :root {
        --brand-indigo: #3D3EEA;
        --brand-glow: rgba(61, 62, 234, 0.22);
        --corner-red: #D20A0A;
        --corner-blue: #2563EB;
        --emerald-win: #10B981;
        --slate-dark: #0F172A;
        --slate-body: #475569;
        --slate-muted: #64748B;
        --card-border: rgba(226, 232, 240, 0.85);
        --card-shadow-ambient: 0 4px 20px -2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.02);
    }

    * {
        letter-spacing: -0.015em;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #0F172A;
        background-color: #FAFAFC !important;
        background-image: 
            radial-gradient(at 50% 0%, rgba(61, 62, 234, 0.07) 0px, transparent 55%),
            radial-gradient(at 100% 0%, rgba(59, 130, 246, 0.04) 0px, transparent 40%),
            radial-gradient(at 0% 50%, rgba(220, 38, 38, 0.025) 0px, transparent 40%) !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }

    #MainMenu, footer, header, [data-testid="stToolbar"] {
        visibility: hidden !important;
        height: 0% !important;
        position: fixed !important;
    }

    .main .block-container {
        max-width: 980px !important;
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
    }

    /* FLUIDE ANIMATION ENTRÉE DE PAGE */
    @keyframes fadeInUpSmooth {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .anim-fade-in {
        animation: fadeInUpSmooth 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* SÉLECTEUR DE LANGUE DISCRET EN HAUT À DROITE */
    div[data-testid="stSelectbox"]:has(div[data-testid="stKey-sb_language_flags"]) div[data-baseweb="select"] {
        border-radius: 9999px !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(14px) !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.25s ease !important;
    }
    div[data-testid="stSelectbox"]:has(div[data-testid="stKey-sb_language_flags"]) div[data-baseweb="select"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08) !important;
        transform: translateY(-1px);
    }

    /* DOCK DE NAVIGATION FLOTTANT (STYLE SEGMENTED CONTROL) */
    div[data-testid="stBaseButton-secondary"] button {
        border-radius: 9999px !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        color: #475569 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 9px 20px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stBaseButton-secondary"] button:hover {
        border-color: #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08) !important;
    }

    /* SÉLECTEURS DE VELADES (DROPDOWN) */
    div[data-testid="stSelectbox"]:not(:has(div[data-testid="stKey-sb_language_flags"])) div[data-baseweb="select"] {
        border-radius: 9999px !important;
        border: 1px solid var(--card-border) !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.25s ease !important;
    }
    div[data-testid="stSelectbox"]:not(:has(div[data-testid="stKey-sb_language_flags"])) div[data-baseweb="select"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.07) !important;
        transform: translateY(-1px);
    }

    /* HERO STAGE OUVERT (ZÉRO BULLE GÉANTE, RESPIRANT, CENTRAGE PARFAIT) */
    .hero-stage-modern {
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 2rem auto 2.6rem auto !important;
        padding: 0 1rem !important;
        max-width: 780px !important;
    }

    .hero-logo-avatar {
        width: 68px;
        height: 68px;
        border-radius: 20px;
        object-fit: cover;
        box-shadow: 0 10px 25px rgba(61, 62, 234, 0.18), 0 2px 6px rgba(15, 23, 42, 0.04);
        border: 2px solid #FFFFFF;
        margin: 0 auto 18px auto;
        display: inline-block;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        animation: floatBreath 4s ease-in-out infinite;
    }
    .hero-logo-avatar:hover {
        transform: scale(1.1) rotate(4deg);
        box-shadow: 0 16px 36px rgba(61, 62, 234, 0.3);
    }
    @keyframes floatBreath {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    .hero-title-modern {
        font-size: 2.85rem !important;
        font-weight: 900 !important;
        color: #0F172A !important;
        letter-spacing: -0.038em !important;
        line-height: 1.15 !important;
        margin: 0 0 14px 0 !important;
        text-align: center !important;
        width: 100% !important;
    }

    .hero-desc-centered {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #475569 !important;
        line-height: 1.72 !important;
        text-align: center !important;
        max-width: 660px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
    }

    /* BENTO CARDS KPI AVEC EFFETS HOVER 3D ET GRADIENT GLOW */
    .bento-card-interactive {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 26px;
        padding: 30px 24px;
        text-align: center;
        box-shadow: var(--card-shadow-ambient);
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
        cursor: default;
    }
    .bento-card-interactive:hover {
        transform: translateY(-6px) scale(1.015);
        border-color: rgba(61, 62, 234, 0.32);
        box-shadow: 0 20px 42px -12px rgba(61, 62, 234, 0.16), 0 4px 12px rgba(15, 23, 42, 0.04);
    }
    .bento-card-green:hover {
        border-color: rgba(16, 185, 129, 0.38) !important;
        box-shadow: 0 20px 42px -12px rgba(16, 185, 129, 0.2), 0 4px 12px rgba(15, 23, 42, 0.04) !important;
    }

    .bento-chip-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.74rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 4px 12px;
        border-radius: 9999px;
        background: #F1F5F9;
        color: #475569;
        margin-bottom: 12px;
        transition: all 0.25s ease;
    }
    .bento-card-interactive:hover .bento-chip-pill {
        background: #EEF2FF;
        color: #3D3EEA;
    }
    .bento-card-green:hover .bento-chip-pill {
        background: #ECFDF5;
        color: #059669;
    }

    .bento-val-huge {
        font-size: 3.4rem;
        font-weight: 900;
        color: #0F172A;
        line-height: 1;
        letter-spacing: -0.04em;
        margin-bottom: 8px;
        font-variant-numeric: tabular-nums;
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .bento-card-interactive:hover .bento-val-huge {
        transform: scale(1.04);
    }
    .bento-val-green {
        color: #10B981 !important;
    }

    .bento-label-clean {
        font-size: 0.85rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* CARTES DE COMBATS AVEC MICRO-ÉLÉVATION AU SURVOL */
    .fight-card-modern {
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 24px;
        padding: 24px 26px;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02), 0 1px 3px rgba(15, 23, 42, 0.02);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
    }
    .fight-card-modern:hover {
        transform: translateY(-4px);
        border-color: #CBD5E1;
        box-shadow: 0 16px 36px -6px rgba(15, 23, 42, 0.07), 0 2px 6px rgba(15, 23, 42, 0.03);
    }

    .summary-card-modern {
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 28px;
        padding: 26px;
        margin-bottom: 26px;
        box-shadow: var(--card-shadow-ambient);
    }

    /* BADGES ÉVÉNEMENT */
    .pill-main-red {
        background: #FEF2F2;
        border: 1px solid #FCA5A5;
        color: #DC2626;
        border-radius: 9999px;
        padding: 5px 14px;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 12px;
    }
    .pill-comain-dark {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        color: #0F172A;
        border-radius: 9999px;
        padding: 5px 14px;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 12px;
    }

    /* SIGNAUX DE PARI ET RECOMMANDATIONS AVEC GLOW VIBRANT */
    .signal-pill-rec {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid #6EE7B7;
        color: #065F46;
        border-radius: 9999px;
        padding: 12px 22px;
        font-size: 0.94rem;
        font-weight: 800;
        text-align: center;
        margin-top: 18px;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.16);
        transition: all 0.25s ease;
    }
    .signal-pill-rec:hover {
        transform: scale(1.01);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.26);
    }
    .signal-pill-no {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #64748B;
        border-radius: 9999px;
        padding: 11px 20px;
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        margin-top: 18px;
    }
    .signal-pill-wait {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        color: #92400E;
        border-radius: 9999px;
        padding: 11px 20px;
        font-size: 0.88rem;
        font-weight: 800;
        text-align: center;
        margin-top: 18px;
    }
    .signal-pill-none {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #64748B;
        border-radius: 9999px;
        padding: 11px 20px;
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        margin-top: 18px;
    }

    /* RÉSULTATS COMBATS PASSÉS */
    .result-pill-win {
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
        border-radius: 14px;
        padding: 12px 20px;
        font-size: 0.92rem;
        font-weight: 700;
        margin-top: 16px;
    }
    .result-pill-loss {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        color: #991B1B;
        border-radius: 14px;
        padding: 12px 20px;
        font-size: 0.92rem;
        font-weight: 700;
        margin-top: 16px;
    }
    .result-pill-nobet {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #64748B;
        border-radius: 14px;
        padding: 12px 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 16px;
    }

    /* ACCORDÉONS STYLE SAAS MODERNE */
    details.aura-accordion {
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 22px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.02);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    details.aura-accordion:hover {
        border-color: #CBD5E1;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        transform: translateY(-1px);
    }
    details.aura-accordion summary {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        cursor: pointer;
        outline: none;
        user-select: none;
        list-style: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    details.aura-accordion summary::-webkit-details-marker {
        display: none;
    }
    details.aura-accordion summary::after {
        content: "▾";
        font-size: 1.15rem;
        color: #64748B;
        transition: transform 0.25s ease;
    }
    details.aura-accordion[open] summary::after {
        transform: rotate(180deg);
        color: var(--brand-indigo);
    }

    /* JAUGES PROGRESSIVES DES 20 VARIABLES IA AVEC HOVER GLOW */
    .feat-meter-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 11px 16px;
        background: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.02);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .feat-meter-row:hover {
        background: #F8FAFC;
        border-color: #CBD5E1;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }
    .feat-bar-bg {
        flex: 1;
        height: 7px;
        background: #F1F5F9;
        border-radius: 9999px;
        overflow: hidden;
        margin: 0 12px;
    }
    .feat-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #4F46E5, #3D3EEA);
        border-radius: 9999px;
        transition: all 0.5s ease;
    }
    .feat-meter-row:hover .feat-bar-fill {
        filter: brightness(1.15);
    }

    /* CONTENEUR DE NOM DE COMBATTANT FIXE POUR ALIGNEMENT PARFAIT */
    .fighter-name-box {
        min-height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 8px;
    }

    /* RESPONSIVE MOBILE 4 COLS -> 2X2 SUR ÉCRANS < 640PX */
    .perf-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        text-align: center;
    }
    @media (max-width: 640px) {
        .perf-stats-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 16px 10px !important;
        }
        .hero-title-modern {
            font-size: 2.1rem !important;
        }
        .bento-val-huge {
            font-size: 2.6rem !important;
        }
    }

    .legal-card-modern {
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 28px;
        padding: 36px 32px;
        margin: 20px 0;
        box-shadow: var(--card-shadow-ambient);
        line-height: 1.75;
        color: #334155;
    }

    .footer-aura {
        text-align: center;
        padding: 2.8rem 0 2rem 0;
        color: #94A3B8;
        font-size: 0.82rem;
        font-weight: 500;
        letter-spacing: 0.02em;
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
    # 🌐 SÉLECTEUR DE LANGUE DISCRET & PERSISTANT (Coin Supérieur Droit)
    lang_map = {"🇬🇧": "EN", "🇫🇷": "FR", "🇪🇸": "ES"}
    reverse_lang_map = {"EN": "🇬🇧", "FR": "🇫🇷", "ES": "🇪🇸"}

    if "lang" in st.query_params and st.query_params["lang"] in ["EN", "FR", "ES"]:
        st.session_state["lang"] = st.query_params["lang"]

    current_lang = st.session_state.get("lang", "EN")
    default_flag = reverse_lang_map.get(current_lang, "🇬🇧")

    col_top_pad, col_top_lang = st.columns([5.4, 1.0])
    with col_top_lang:
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

    # Router Session State
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

    # 🖼️ INJECTION DES BALISES META OPEN GRAPH DYNAMIQUES (MMA VISION)
    og_img_url = get_og_image_url()
    st.components.v1.html(f"""
    <script>
    try {{
        const doc = window.parent.document;
        const metaTags = [
            {{ property: 'og:title', content: 'MMA Vision — MMA Analytics & Predictions' }},
            {{ property: 'og:description', content: 'Premier MMA Prediction Bot powered by AI.' }},
            {{ property: 'og:image', content: '{og_img_url}' }},
            {{ property: 'og:url', content: 'https://mmavision.com' }},
            {{ property: 'og:type', content: 'website' }},
            {{ name: 'twitter:card', content: 'summary_large_image' }},
            {{ name: 'twitter:title', content: 'MMA Vision — MMA Analytics & Predictions' }},
            {{ name: 'twitter:description', content: 'Premier MMA Prediction Bot powered by AI.' }},
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

    # 🍪 SÉCURISATION & PERSISTANCE DU CONSENTEMENT COOKIE
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

        const consent = urlParams.get('cookie_consent');
        if (consent) {{
            parentWin.localStorage.setItem('mma_cookie_consent', consent);
            parentWin.localStorage.setItem('ufc_cookie_consent', consent);
            urlParams.delete('cookie_consent');
            const cleanSearch = urlParams.toString() ? ('?' + urlParams.toString()) : '';
            const cleanUrl = parentWin.location.pathname + cleanSearch + parentWin.location.hash;
            parentWin.history.replaceState({{}}, parentWin.document.title, cleanUrl);
        }} else {{
            const savedConsent = parentWin.localStorage.getItem('mma_cookie_consent') || parentWin.localStorage.getItem('ufc_cookie_consent');
            if (savedConsent && !urlParams.has('cookie_consent')) {{
                const url = new URL(parentWin.location.href);
                url.searchParams.set("cookie_consent", savedConsent);
                parentWin.location.replace(url.toString());
            }}
        }}

        let currentLang = '{current_lang}';
        if (currentLang) {{
            parentWin.localStorage.setItem('mma_lang', currentLang);
            parentWin.localStorage.setItem('ufc_lang', currentLang);
        }}
    }} catch(e) {{}}
    </script>
    """, height=0, width=0)

    # DÉCLENCHEMENT POP-UP DIALOG COOKIES NATIVE SI PAS ENCORE DE CONSENTEMENT
    if not st.session_state.get("cookie_consent") and "cookie_consent" not in st.query_params:
        show_cookie_dialog(t)

    # ⚡ CHARGEMENT PASSIF ULTRA-RAPIDE VIA LA COUCHE SERVICE (0 calcul ML lourd)
    upcoming_cards = get_upcoming_cards()
    past_cards = get_past_cards()
    fin_summary = get_financial_summary()
    odds_meta = get_odds_metadata()
    odds_age_mins = odds_meta.get("age_mins", 1)
    odds_age_hours = int(odds_meta.get("age_hours", 0))
    odds_remaining_mins = odds_age_mins % 60

    # 🏛️ BANDEAU DE NAVIGATION PARFAITEMENT CENTRÉ
    c_pad_l, c_nav_box, c_pad_r = st.columns([0.6, 3.2, 0.6])

    with c_nav_box:
        c_left, c_center, c_right = st.columns([1.3, 1.1, 1.3])

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

    current_page = st.session_state.get("current_page", "home")
    if current_page == "past":
        active_btn_key = "btn_nav_past"
    elif current_page == "upcoming":
        active_btn_key = "btn_nav_upcoming"
    else:
        active_btn_key = "btn_nav_home"

    logo_data_url = get_logo_base64()

    # Stylisation dynamique de l'onglet actif en pilule pleine vibrante
    st.markdown(f"""
    <style>
        div[data-testid="stKey-{active_btn_key}"] button,
        button[data-testid="stBaseButton-{active_btn_key}"] {{
            background: linear-gradient(135deg, #4F46E5 0%, #3D3EEA 100%) !important;
            color: #FFFFFF !important;
            border-color: #3D3EEA !important;
            box-shadow: 0 6px 20px rgba(61, 62, 234, 0.32) !important;
            font-weight: 800 !important;
            transform: translateY(-1.5px) !important;
        }}
        div[data-testid="stKey-{active_btn_key}"] button p,
        div[data-testid="stKey-{active_btn_key}"] button span {{
            color: #FFFFFF !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    page = current_page

    # =========================================================================
    # PAGE 1 : 🏠 ACCUEIL
    # =========================================================================
    if page == "home":
        # HERO SECTION OUVERTE : Logo compact en apesanteur, typographie percutante, centrage parfait
        render_clean_html(f"""
        <div class="hero-stage-modern anim-fade-in">
            <img src="{logo_data_url}" alt="MMA Vision" class="hero-logo-avatar">
            <h1 class="hero-title-modern">
                {t['hero_subtitle']}
            </h1>
            <p class="hero-desc-centered">
                {t['hero_description']}
            </p>
        </div>
        """)

        # BENTO CARDS KPI AVEC EFFETS HOVER 3D
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            render_clean_html(f"""
            <div class="bento-card-interactive anim-fade-in">
                <span class="bento-chip-pill">{t['verified_badge']}</span>
                <div class="bento-val-huge">69 %</div>
                <div class="bento-label-clean">{t['stat_winrate_desc']}</div>
            </div>
            """)

        with col_m2:
            render_clean_html(f"""
            <div class="bento-card-interactive bento-card-green anim-fade-in">
                <span class="bento-chip-pill">{t['cumulative_edge']}</span>
                <div class="bento-val-huge bento-val-green">+31 %</div>
                <div class="bento-label-clean">{t['stat_roi_desc']}</div>
            </div>
            """)

        # 📊 ACCORDÉON DES 20 VARIABLES IA AVEC JAUGES PROGRESSIVES ET EFFET HOVER GLIDE
        feat_importances = get_feature_importances(current_lang)
        feat_items_list = []
        max_pct = max([p for _, _, p in feat_importances]) if feat_importances else 100.0

        for rank, (col, label, pct) in enumerate(feat_importances, 1):
            bar_width = min(100.0, (pct / max_pct) * 100.0) if max_pct > 0 else 50.0
            feat_items_list.append(f"""
            <div class="feat-meter-row">
                <span style="font-weight: 800; font-size: 0.8rem; color: #64748B; width: 30px;">#{rank:02d}</span>
                <span style="font-weight: 700; color: #0F172A; font-size: 0.88rem; flex: 1.2;">{label}</span>
                <div class="feat-bar-bg">
                    <div class="feat-bar-fill" style="width: {bar_width:.1f}%;"></div>
                </div>
                <span style="font-weight: 800; color: #3D3EEA; font-size: 0.88rem; min-width: 48px; text-align: right;">{pct:.1f}%</span>
            </div>
            """)
        feature_items_html = "\n".join(feat_items_list)

        render_clean_html(f"""
        <div style="margin-top: 2.5rem;" class="anim-fade-in">
            <details class="aura-accordion" style="margin-bottom: 1.25rem;">
                <summary><b>{t['feature_importance_title']}</b></summary>
                <div style="padding-top: 16px;">
                    <p style="margin-bottom: 16px; color: #475569; font-size: 0.92rem; line-height: 1.6;">
                        {t['feature_importance_desc']}
                    </p>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        {feature_items_html}
                    </div>
                </div>
            </details>

            <details class="aura-accordion">
                <summary><b>{t['faq_title']}</b></summary>
                <div style="padding-top: 16px; display: flex; flex-direction: column; gap: 14px;">
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q1']}</div>
                        <div style="color: #475569; font-size: 0.94rem; line-height: 1.6;">{t['a1']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q2']}</div>
                        <div style="color: #475569; font-size: 0.94rem; line-height: 1.6;">{t['a2']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q3']}</div>
                        <div style="color: #475569; font-size: 0.94rem; line-height: 1.6;">{t['a3']}</div>
                    </div>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">{t['q4']}</div>
                        <div style="color: #475569; font-size: 0.94rem; line-height: 1.6;">{t['a4']}</div>
                    </div>
                    <div style="margin-top: 6px; font-weight: 700; color: #3D3EEA; font-size: 0.88rem;">
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

        if odds_age_hours >= 1:
            freshness_str = t["odds_updated_hours"].format(hours=odds_age_hours, mins=odds_remaining_mins)
        else:
            freshness_str = t["odds_updated_mins"].format(mins=odds_age_mins)

        render_clean_html(f"""
        <div style="text-align: right; margin-bottom: 14px; font-size: 0.8rem; font-weight: 700; color: #64748B;">
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
                    html_card = f"""<div class="fight-card-modern anim-fade-in">
{badge_html}
<h3 style="margin: 6px 0 16px 0; font-size: 1.35rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
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

                html_card = f"""<div class="fight-card-modern anim-fade-in">
{badge_html}
<h3 style="margin: 6px 0 18px 0; font-size: 1.35rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
<div style="display: flex; gap: 20px; margin-bottom: 16px;">
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.92rem; font-weight: 800; color: #64748B;">🔴 {f1_raw}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1; font-variant-numeric: tabular-nums;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: {odds_color}; margin: 4px 0 8px 0;">{odds_a_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%); height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.92rem; font-weight: 800; color: #64748B;">🔵 {f2_raw}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1; font-variant-numeric: tabular-nums;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: {odds_color}; margin: 4px 0 8px 0;">{odds_b_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%); height: 100%; border-radius: 9999px;"></div>
</div>
</div>
</div>
{signal_html}
</div>"""
                render_clean_html(html_card)

    # =========================================================================
    # PAGE 3 : 📜 COMBATS ANTÉRIEURS (POINT-IN-TIME SANS DATA LEAKAGE)
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

        html_summary_card = f"""<div class="summary-card-modern anim-fade-in">
<div style="font-size: 0.84rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 18px; text-align: center;">
    {t.get('global_summary_title', '🌐 Global Performance')}
</div>
<div class="perf-stats-grid">
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['net_profit']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: {global_prof_color}; margin-top: 4px; font-variant-numeric: tabular-nums;">{tot_prof:+.2f} €</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{t['volume_sub'].format(staked=tot_stake, bets=v_count)}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['roi_yield']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{global_roi_formatted}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['win_rate_value']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{win_r:.1f}%</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{v_won}/{v_count} {t['won_text']}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['accuracy_all']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{overall_acc:.1f}%</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{tot_correct}/{tot_valid} {t['correct_text']}</div>
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

            html_card_summary = f"""<div class="summary-card-modern anim-fade-in" style="margin-top: 14px; margin-bottom: 24px;">
<div style="font-size: 0.84rem; font-weight: 800; color: #3D3EEA; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 18px; text-align: center;">
    {t.get('card_summary_title', '📅 Event Performance')}
</div>
<div class="perf-stats-grid">
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['net_profit']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: {card_prof_color}; margin-top: 4px; font-variant-numeric: tabular-nums;">{card_profit:+.2f} €</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{t['volume_sub'].format(staked=card_staked, bets=card_vb_count)}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['roi_yield']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{card_roi_formatted}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['win_rate_value']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{card_win_rate:.1f}%</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{card_vb_won}/{card_vb_count} {t['won_text']}</div>
</div>
<div>
<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{t['accuracy_all']}</div>
<div style="font-size: 1.85rem; font-weight: 900; color: #0F172A; margin-top: 4px; font-variant-numeric: tabular-nums;">{card_accuracy:.1f}%</div>
<div style="font-size: 0.76rem; font-weight: 600; color: #94A3B8; margin-top: 4px;">{card_correct_count}/{card_total_valid_fights} {t['correct_text']}</div>
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
    <span style="font-size: 0.92rem; font-weight: 800; color: #64748B;">🔴 {pf1}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1; font-variant-numeric: tabular-nums;">{pct_a:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_a_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_a:.1f}%; background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%); height: 100%; border-radius: 9999px;"></div>
</div>
</div>
<div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
<div class="fighter-name-box">
    <span style="font-size: 0.92rem; font-weight: 800; color: #64748B;">🔵 {pf2}</span>
</div>
<div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1; font-variant-numeric: tabular-nums;">{pct_b:.1f}%</div>
<div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">{odds_b_str}</div>
<div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
<div style="width: {pct_b:.1f}%; background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%); height: 100%; border-radius: 9999px;"></div>
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

                html_past_card = f"""<div class="fight-card-modern anim-fade-in">
{badge_html}
<h3 style="margin: 6px 0 18px 0; font-size: 1.35rem; font-weight: 800; color: #0F172A;">{pf1} vs {pf2}</h3>
{metrics_html}
{res_html}
</div>"""
                render_clean_html(html_past_card)

    # =========================================================================
    # PAGE 4 : ⚖️ MENTIONS LÉGALES & CONFIDENTIALITÉ
    # =========================================================================
    elif page == "legal":
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
        <div class="legal-card-modern anim-fade-in">
            <h4 style="color: #0F172A; margin-top: 0; font-weight: 800;">{t['legal_sec1_title']}</h4>
            <p>{t['legal_publisher']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec2_title']}</h4>
            <p>{t['legal_hosting']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec3_title']}</h4>
            <p>{t['legal_ip']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec4_title']}</h4>
            <p>{t['legal_privacy']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec5_title']}</h4>
            <p>{t['disclaimer_ai']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec6_title']}</h4>
            <p>{t['disclaimer_gaming']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec7_title']}</h4>
            <p>{t['disclaimer_trademark']}</p>

            <h4 style="color: #0F172A; margin-top: 1.6rem; font-weight: 800;">{t['legal_sec8_title']}</h4>
            <p>{t['legal_ads']}</p>

            <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 24px 0;">
            <p style="font-weight: 700; color: #3D3EEA;">{t['bug_contact']}</p>
        </div>
        """)

        if st.button(t["back_home"], key="btn_back_home_bottom"):
            st.session_state["current_page"] = "home"
            st.rerun()

    # =========================================================================
    # FOOTER COMMUN (BOUTON MENTIONS LÉGALES & FOOTER)
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
