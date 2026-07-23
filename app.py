"""
UFC Predictor - Application Web SaaS High-End (Design system "Aura Dev" - Glassmorphism & Floating Pills)
Garantit la protection intégrale et l'inviolabilité du backend (src/, models/, data/).
Interface 100% HTML/CSS pure pour le rendu des cartes de combat en bulles Blanc Pur (#FFFFFF).
"""

import os
import sys
import json
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


def render_clean_html(html_str):
    """
    Supprime tous les espaces d'indentation au début de chaque ligne HTML.
    Évite rigoureusement que Markdown n'interprète la ligne comme un bloc de code (règle des 4 espaces).
    """
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# 1. Configuration de la Page Streamlit
st.set_page_config(
    page_title="UFC Predictor — Le meilleur bot de prédiction de l'UFC",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Design System "Aura Dev" Glassmorphism & Floating Pills CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
    
    /* 1. Masquer le header et la toolbar Streamlit */
    [data-testid="stHeader"], header, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. Annuler tout le rembourrage supérieur de la page */
    [data-testid="stAppViewContainer"] > .main, 
    .main .block-container, 
    div[data-testid="stMainBlockContainer"] {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        padding-bottom: 2rem !important;
        max-width: 1050px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        color: #0F172A;
    }
    
    /* Fond général du site : GRIS CLAIR #F1F5F9 */
    .stApp, 
    [data-testid="stAppViewContainer"], 
    body {
        background-color: #F1F5F9 !important;
        background: #F1F5F9 !important;
    }

    /* Style des 3 boutons pilules du header (Aucun débordement de texte) */
    .stButton > button {
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
    }

    .stButton > button:hover {
        border-color: #D20A0A !important;
        color: #D20A0A !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(210, 10, 10, 0.12) !important;
    }

    /* CLASSES SPECIFIQUES POUR LES BULLES DE COMBAT ET SUMMARY (BLANC PUR #FFFFFF GARANTI) */
    .fight-card-pure-white {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
    }

    .summary-card-pure-white {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
    }

    /* Badges de combat */
    .pill-main-red {
        background-color: #D20A0A !important;
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    .pill-comain-dark {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    /* Action Signal Pills (Prochains combats) */
    .signal-pill-rec {
        background-color: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        border-left: 6px solid #10B981 !important;
        color: #065F46 !important;
        padding: 0.9rem 1.2rem;
        border-radius: 18px;
        font-weight: 700;
        margin-top: 0.8rem;
    }

    .signal-pill-no {
        background-color: #FFF7ED !important;
        border: 1px solid #FFEDD5 !important;
        border-left: 6px solid #F97316 !important;
        color: #9A3412 !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }

    .signal-pill-wait {
        background-color: #FEFCE8 !important;
        border: 1px solid #FEF08A !important;
        border-left: 6px solid #EAB308 !important;
        color: #854D0E !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }

    .signal-pill-none {
        background-color: #F0F9FF !important;
        border: 1px solid #BAE6FD !important;
        border-left: 6px solid #3B82F6 !important;
        color: #075985 !important;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        font-weight: 600;
        margin-top: 0.8rem;
    }

    /* Result Pills (Combats passés) */
    .result-pill-win {
        background-color: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        color: #065F46 !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        margin-top: 0.8rem !important;
    }

    .result-pill-loss {
        background-color: #FEF2F2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #991B1B !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        margin-top: 0.8rem !important;
    }

    .result-pill-nobet {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #475569 !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 16px !important;
        font-size: 0.88rem !important;
        margin-top: 0.8rem !important;
    }

    .hero-bubble {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 40px !important;
        padding: 3.5rem 2rem 2.5rem 2rem !important;
        text-align: center !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04) !important;
        margin: 4.5rem auto 2.5rem auto !important;
    }

    /* Stat Cards (Bulles Blanc Pur Côtes à Côtes) */
    .stat-pill {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 32px !important;
        padding: 2rem 1.5rem !important;
        text-align: center !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03) !important;
    }

    .stat-val-huge {
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #D20A0A;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .stat-desc-clean {
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569;
    }

    .footer-aura {
        text-align: center;
        padding: 5rem 0 2.5rem 0;
        margin-top: 6rem !important;
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# FONCTIONS DE CACHING STREAMLIT HAUTE PERFORMANCE (NAV INSTANTANÉE)
# =========================================================================

@st.cache_resource
def load_all_models_and_data():
    """Mise en cache du modèle XGBoost V3 et des structures de données statiques."""
    return load_resources_v3()


@st.cache_data(ttl=7200)
def get_cached_odds_data():
    """Mise en cache 2h des cotes The Odds API."""
    return get_cached_or_fresh_odds()


@st.cache_resource
def get_cached_tracker_data(events, _raw_df, _model, _medians, _all_fighters):
    """Mise en cache du tracker d'historique et des prédictions des cartes passées & futures."""
    return sync_historical_tracker(events, _raw_df, _model, _medians, _all_fighters)


@st.cache_resource
def get_cached_dynamic_states(_raw_df):
    """Mise en cache du calcul des ELOs et streaks sur les 8,784 combats de l'historique."""
    return compute_fighter_dynamic_states_v3(_raw_df)


@st.cache_resource
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
    # Session State Router (Intact)
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "home"

    # Chargement Backend Intact Optimisé via Streamlit Cache
    events, from_cache, age_hours = get_cached_odds_data()
    try:
        model, raw_df, medians, all_fighters, model_path_used = load_all_models_and_data()
    except Exception as e:
        st.error(f"Erreur d'initialisation du modèle : {e}")
        st.stop()

    upcoming_cards, past_cards, fin_summary = get_cached_tracker_data(events, raw_df, model, medians, all_fighters)
    elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = get_cached_dynamic_states(raw_df)

    # BANDEAU DE NAVIGATION CENTRÉ
    c_pad_l, c_nav_box, c_pad_r = st.columns([0.7, 2.6, 0.7])

    with c_nav_box:
        c_left, c_center, c_right = st.columns([1.35, 1.0, 1.35])

        with c_left:
            if st.button("📜 Combats Antérieurs", key="btn_nav_past", use_container_width=True):
                st.session_state["current_page"] = "past"
                st.rerun()

        with c_center:
            if st.button("🥊 UFC Predictor", key="btn_nav_home", use_container_width=True):
                st.session_state["current_page"] = "home"
                st.rerun()

        with c_right:
            if st.button("🔮 Combats Futurs", key="btn_nav_upcoming", use_container_width=True):
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
            border-color: #D20A0A !important;
            color: #D20A0A !important;
            box-shadow: 0 4px 14px rgba(210, 10, 10, 0.18) !important;
            font-weight: 800 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    page = current_page

    # =========================================================================
    # PAGE 1 : 🏠 ACCUEIL (HERO BUBBLE BLANC PUR)
    # =========================================================================
    if page == "home":
        render_clean_html("""
        <div class="hero-bubble">
            <h1 style="font-size: 3.5rem; font-weight: 900; letter-spacing: -0.04em; margin: 0 0 0.4rem 0;">
                <span style="color:#D20A0A;">UFC</span> <span style="color:#0F172A;">Predictor</span>
            </h1>
            <p style="font-size: 1.25rem; font-weight: 600; color: #475569; margin: 0;">
                Le meilleur bot de prédiction de l'UFC
            </p>
        </div>
        """)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            render_clean_html("""
            <div class="stat-pill">
                <div class="stat-val-huge">69 %</div>
                <div class="stat-desc-clean">Winrate du bot de 2015 à 2026</div>
            </div>
            """)

        with col_m2:
            render_clean_html("""
            <div class="stat-pill">
                <div class="stat-val-huge">+31 %</div>
                <div class="stat-desc-clean">ROI du bot de 2015 à 2026</div>
            </div>
            """)

    # =========================================================================
    # PAGE 2 : 🔮 COMBATS FUTURS (BULLES BLANC PUR SUR FOND GRIS EN PURE HTML)
    # =========================================================================
    elif page == "upcoming":
        st.markdown("### 🔮 Prédictions des Prochains Événements UFC")

        if not upcoming_cards:
            st.info("ℹ️ Aucune carte future disponible pour le moment.")
        else:
            chronological_keys = list(upcoming_cards.keys())

            selected_card_key = st.selectbox(
                "Sélectionnez une carte UFC à venir :",
                chronological_keys,
                format_func=lambda k: f"🗓️ {k} ({len(upcoming_cards[k].get('fights', []))} combats)",
                key="sb_upcoming"
            )

            card_info = upcoming_cards[selected_card_key]
            selected_events = deduplicate_card_fights(card_info.get("fights", []))

            for idx, ev in enumerate(selected_events, 1):
                f1_raw = ev.get("f1") or ev.get("home_team", "")
                f2_raw = ev.get("f2") or ev.get("away_team", "")
                fight_label = ev.get("fight_label", f"Combat #{idx}")

                name_a = resolve_fighter_name(f1_raw, all_fighters)
                name_b = resolve_fighter_name(f2_raw, all_fighters)

                profile_a = get_cached_fighter_profile(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None
                profile_b = get_cached_fighter_profile(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_b else None

                odds_a, odds_b, bkm_name = extract_fight_odds(ev, name_a or f1_raw, name_b or f2_raw)

                has_full_data = bool(name_a and name_b and profile_a is not None and profile_b is not None)
                has_valid_odds = bool(odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0)

                # Badge Main Event / Co-Main Event
                badge_html = ""
                if fight_label == "MAIN EVENT":
                    badge_html = '<span class="pill-main-red">🔥 MAIN EVENT</span>'
                elif fight_label == "CO-MAIN EVENT":
                    badge_html = '<span class="pill-comain-dark">⭐ CO-MAIN EVENT</span>'

                # CAS 1 : DONNÉES INSUFFISANTES
                if not has_full_data:
                    signal_html = '<div class="signal-pill-none">🔘 <b>DONNÉES INSUFFISANTES</b> — Historique UFC incomplet.</div>'
                    html_card = f"""
                    <div class="fight-card-pure-white">
                        {badge_html}
                        <h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
                        {signal_html}
                    </div>
                    """
                    render_clean_html(html_card)
                    continue

                # CALCUL IA V3 (Intact)
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

                    # CAS 2 : COTES EN ATTENTE
                    if not has_valid_odds:
                        signal_html = '<div class="signal-pill-wait">⏳ <b>COTES EN ATTENTE</b> — En attente des cotes officielles.</div>'
                        html_card = f"""
                        <div class="fight-card-pure-white">
                            {badge_html}
                            <h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
                            <div style="display: flex; gap: 20px; margin-bottom: 16px;">
                                <div style="flex: 1;">
                                    <div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔴 {f1_raw}</div>
                                    <div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
                                    <div style="font-size: 0.85rem; font-weight: 700; color: #94A3B8; margin: 4px 0 8px 0;">Cote : N/A</div>
                                    <div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
                                        <div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
                                    </div>
                                </div>
                                <div style="flex: 1;">
                                    <div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔵 {f2_raw}</div>
                                    <div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
                                    <div style="font-size: 0.85rem; font-weight: 700; color: #94A3B8; margin: 4px 0 8px 0;">Cote : N/A</div>
                                    <div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
                                        <div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
                                    </div>
                                </div>
                            </div>
                            {signal_html}
                        </div>
                        """
                        render_clean_html(html_card)
                        continue

                    # CAS 3 : COTES DISPONIBLES ET BADGES D'ACTION
                    ev_a = (prob_a_win * odds_a) - 1.0
                    ev_b = (prob_b_loss * odds_b) - 1.0
                    best_ev = max(ev_a, ev_b)
                    best_fighter = f1_raw if ev_a >= ev_b else f2_raw

                    if best_ev > 0.20:
                        signal_html = f'<div class="signal-pill-rec">🟢 <b>PARI RECOMMANDÉ SUR {best_fighter.upper()}</b></div>'
                    else:
                        signal_html = '<div class="signal-pill-no">🚨 <b>PAS DE PARI RECOMMANDE</b></div>'

                    html_card = f"""
                    <div class="fight-card-pure-white">
                        {badge_html}
                        <h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{f1_raw} vs {f2_raw}</h3>
                        <div style="display: flex; gap: 20px; margin-bottom: 16px;">
                            <div style="flex: 1;">
                                <div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔴 {f1_raw}</div>
                                <div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_a:.1f}%</div>
                                <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">Cote : {odds_a:.2f}</div>
                                <div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
                                    <div style="width: {pct_a:.1f}%; background-color: #D20A0A; height: 100%; border-radius: 9999px;"></div>
                                </div>
                            </div>
                            <div style="flex: 1;">
                                <div style="font-size: 0.9rem; font-weight: 700; color: #64748B; margin-bottom: 4px;">🔵 {f2_raw}</div>
                                <div style="font-size: 2.2rem; font-weight: 900; color: #0F172A; line-height: 1;">{pct_b:.1f}%</div>
                                <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 4px 0 8px 0;">Cote : {odds_b:.2f}</div>
                                <div style="width: 100%; background-color: #E2E8F0; border-radius: 9999px; height: 8px;">
                                    <div style="width: {pct_b:.1f}%; background-color: #3B82F6; height: 100%; border-radius: 9999px;"></div>
                                </div>
                            </div>
                        </div>
                        {signal_html}
                    </div>
                    """
                    render_clean_html(html_card)

                except Exception as ex:
                    st.error(f"Erreur d'affichage : {ex}")

    # =========================================================================
    # PAGE 3 : 📜 COMBATS ANTÉRIEURS (BULLES BLANC PUR SUR FOND GRIS EN PURE HTML)
    # =========================================================================
    elif page == "past":
        st.markdown("### 📊 Performance Réelle (Mise Fictive 10 €)")

        tot_prof = fin_summary.get("total_profit", 0.0)
        tot_stake = fin_summary.get("total_staked", 0.0)
        roi_p = fin_summary.get("roi_pct", 0.0)
        win_r = fin_summary.get("win_rate_pct", 0.0)
        v_count = fin_summary.get("value_bets_count", 0)
        v_won = fin_summary.get("value_bets_won", 0)

        # Carte de Bilan Financier en Pure HTML Blanc Pur
        html_summary_card = f"""
        <div class="summary-card-pure-white">
            <div style="display: flex; gap: 16px; text-align: center;">
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">💵 Profit Net Total</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #10B981;">{tot_prof:+.2f} €</div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #10B981;">{roi_p:+.1f}% ROI</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">📈 Rendement ROI</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{roi_p:.1f}%</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">🎯 Taux de Réussite</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{win_r:.1f}%</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{v_won}/{v_count} gagnés</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #64748B;">💶 Volume Misé</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{tot_stake:.0f} €</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">{v_count} paris</div>
                </div>
            </div>
        </div>
        """
        render_clean_html(html_summary_card)

        if not past_cards:
            st.info("ℹ️ Aucune carte passée archivée depuis le 19 Juillet 2026.")
        else:
            past_keys = list(past_cards.keys())

            selected_past_key = st.selectbox(
                "Sélectionnez une soirée UFC passée :",
                past_keys,
                format_func=lambda k: f"📜 {k} ({len(deduplicate_card_fights(past_cards[k].get('fights', [])))} combats)",
                key="sb_past"
            )

            p_card_info = past_cards[selected_past_key]
            p_fights = deduplicate_card_fights(p_card_info.get("fights", []))

            for idx, fight in enumerate(p_fights, 1):
                pf1 = fight.get("f1", "")
                pf2 = fight.get("f2", "")
                flabel = fight.get("fight_label", f"Combat #{idx}")
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

                # Badge Main Event / Co-Main Event
                badge_html = ""
                if flabel == "MAIN EVENT":
                    badge_html = '<span class="pill-main-red">🔥 MAIN EVENT</span>'
                elif flabel == "CO-MAIN EVENT":
                    badge_html = '<span class="pill-comain-dark">⭐ CO-MAIN EVENT</span>'

                # Probabilités et Cotes (si disponibles)
                metrics_html = ""
                if pct_a is not None and pct_b is not None:
                    odds_a_str = f"Cote : {fight.get('odds_a', 0.0):.2f}" if fight.get('odds_a') else "Cote : N/A"
                    odds_b_str = f"Cote : {fight.get('odds_b', 0.0):.2f}" if fight.get('odds_b') else "Cote : N/A"
                    metrics_html = f"""
                    <div style="display: flex; gap: 20px; margin-bottom: 16px;">
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
                    </div>
                    """

                # Pavé de Résultat Personnalisé
                if is_vb and res_status == "WIN":
                    res_html = f'<div class="result-pill-win">🟢 <b>GAGNÉ (+{net_gain:.2f} €)</b> — Pari réussi sur <b>{bet_f}</b> (Cote : <b>{b_odds:.2f}</b>). Vainqueur : <b>{winner}</b>.</div>'
                elif is_vb and res_status == "LOSS":
                    res_html = f'<div class="result-pill-loss">🔴 <b>PERDU (-10.00 €)</b> — Pari engagé sur <b>{bet_f}</b> (Cote : <b>{b_odds:.2f}</b>). Vainqueur : <b>{winner}</b>.</div>'
                else:
                    if not has_full:
                        res_html = f'<div class="result-pill-nobet">⚪ <b>NO BET — Données insuffisantes</b><br><span style="font-size:0.82rem; color:#64748B;">Pari annulé : Historique UFC insuffisant pour au moins un combattant. Vainqueur : <b>{winner or "N/A"}</b>.</span></div>'
                    elif not has_odds:
                        res_html = f'<div class="result-pill-nobet">⚪ <b>NO BET — Cotes indisponibles</b><br><span style="font-size:0.82rem; color:#64748B;">Pari annulé : Aucune cote publiée avant le combat. Vainqueur : <b>{winner or "N/A"}</b>.</span></div>'
                    else:
                        if max_ev_val is None:
                            best_ev_f = max(ev_a_val, ev_b_val) if (ev_a_val is not None and ev_b_val is not None) else 0.0
                            max_ev_val = best_ev_f * 100.0
                        res_html = f'<div class="result-pill-nobet">⚪ <b>NO BET — Pas de Value Bet (EV max : {max_ev_val:+.1f}%)</b><br><span style="font-size:0.82rem; color:#64748B;">Pari évité : Valeur insuffisante. Vainqueur : <b>{winner or "N/A"}</b>.</span></div>'

                html_past_card = f"""
                <div class="fight-card-pure-white">
                    {badge_html}
                    <h3 style="margin: 8px 0 20px 0; font-size: 1.4rem; font-weight: 800; color: #0F172A;">{pf1} vs {pf2}</h3>
                    {metrics_html}
                    {res_html}
                </div>
                """
                render_clean_html(html_past_card)

    # FOOTER DISCRET AURA DEV
    render_clean_html("""
    <div class="footer-aura">
        UFC Predictor © 2026 — Tous droits réservés | Jeu Responsable (+18)
    </div>
    """)


if __name__ == "__main__":
    main()