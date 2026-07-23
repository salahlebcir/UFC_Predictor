# 🥊 UFC Fight Predictor - Prédiction de Combats UFC (XGBoost V3)

Un système complet de prédiction de combats d'arts martiaux mixtes (UFC) développé en Python avec **XGBoost**, une **ingénierie temporelle avancée (V2)**, un **filtrage par époque (Ère Moderne 2010–2026)**, des **fenêtres glissantes sur 3 ans (36 mois)** et une **pondération temporelle par dépréciation (Time Decay $\lambda=0.15$)**.

---

## 🚀 Performances & Comparaison Tri-Modèle

| Version | Période & Fonctionnalités | Accuracy Test Set | ROC-AUC | Top Facteurs Clés |
| :--- | :--- | :---: | :---: | :--- |
| **V1** | 1994–2026 (11 Features V1) | 64.77 % | 0.6950 | SlpM, Precision frappe, SApM |
| **V2** | 1994–2026 (20 Features V1+V2 : Elo, Streaks, Rang) | 69.52 % | 0.7539 | Rang Officiel (15.25%), Status Top 15, SlpM |
| **V3** 💥 | **2010–2026 (24 Features : Ère Moderne + Fenêtres 3 ans + Time Decay $\lambda=0.15$)** | **68.43 %** | **0.7492** | **Status Top 15 (18.05%), Difference Rang (16.08%), Str Acc** |

---

## 🧠 Innovations Technologiques du Module V3

### 1. Filtrage par Époque (Ère Moderne 2010–2026)
Les combats des années 1990 et début 2000 obéissaient à des règles et métas dépassées.
- **Calcul Historique Intégral** : L'accumulation d'expérience et l'Elo démarrant au tout premier combat de 1994 pour restituer l'historique exact pre-fight.
- **Filtrage Échantillon ML** : Seuls les combats se déroulant du **01/01/2010 au 18/07/2026** (7 378 combats) constituent le dataset d'entraînement et d'évaluation du modèle.

### 2. Caractéristiques à Fenêtres Glissantes (3 ans / 36 mois)
Calcul dynamique des statistiques glissantes pre-fight sur les 36 mois précédant l'événement :
- `delta_win_rate_3y` : Différence du taux de victoire récent.
- `delta_SlpM_3y` : Différence de cadence de frappe récente.
- `delta_SApM_3y` : Différence de vulnérabilité aux frappes récente.
- `delta_TD_Def_3y` : Différence de défense contre les takedowns récente.

### 3. Dépréciation Temporelle des Échantillons (*Time Decay*)
Un poids d'échantillon $w_i$ est attribué à chaque combat selon sa récence par rapport au combat le plus récent $T_{\text{max}} = \text{18/07/2026}$ :

$$w_i = \exp\left(-0.15 \cdot \frac{T_{\text{max}} - t_i}{365.25}\right)$$

Les combats récents reçoivent un poids proche de 1.0, tandis que les combats plus anciens voient leur poids décroître naturellement.

---

## 📁 Arborescence du Projet

```text
UFC_PREDICATOR/
├── data/
│   ├── raw/
│   │   └── UFC_full_data_silver_v2.csv      # Jeu de données d'origine (8 784 combats)
│   └── processed/
│       ├── ufc_features_delta_v3.csv        # Dataset V3 nettoyé (2010-2026, 24 caractéristiques)
│       └── feature_medians_v3.json          # Médianes d'imputation V3
├── models/
│   ├── ufc_xgboost_model_v3.pkl             # Modèle XGBoost V3 (Ère Moderne + Time Decay)
│   └── model_metadata_v3.json               # Métriques et Feature Importances V3
├── src/
│   ├── __init__.py                          # Initialisation du module Python
│   ├── data_prep.py                         # Calculs temporels V3, fenêtres 3 ans & filtrage 2010-2026
│   ├── train.py                             # Entraînement XGBoost V3 avec sample_weight
│   └── predict.py                           # CLI de prédiction V3 avec Fuzzy Matching
├── requirements.txt                         # Dépendances Python
└── README.md                                # Documentation du projet
```

---

## ⚙️ Installation & Guide d'Utilisation V3

1. Activer l'environnement virtuel et installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

2. Exécuter la préparation des données V3 :
   ```bash
   python src/data_prep.py
   ```

3. Ré-entraîner le modèle XGBoost V3 :
   ```bash
   python src/train.py
   ```

4. Lancer une prédiction V3 (CLI) :
   ```bash
   python src/predict.py --f1 "Dricus Du Plessis" --f2 "Kamaru Usman"
   ```

*Exemple de sortie CLI V3 :*
```text
=================================================================
      RESULTAT DU PRONOSTIC UFC V3 (Ère Moderne + Time Decay)
=================================================================

   [Combattant A] : Dricus Du Plessis
   [Combattant B] : Kamaru Usman

-----------------------------------------------------------------
 [VAINQUEUR PREDIT] : Dricus Du Plessis (77.9% de confiance)
-----------------------------------------------------------------

 [PROBABILITES DE VICTOIRE] :
    * Dricus Du Plessis         : 77.9%
    * Kamaru Usman              : 22.1%

 [TOP 3 DES FACTEURS CLES DU COMBAT] :
    1. Classement Officiel UFC (Difference de Rang)
       Delta = +7.00 (Avantage Dricus Du Plessis)
    2. Age (Annees)
       Delta = -6.68 (Avantage Kamaru Usman)
    3. Combattant A fait partie du Top 15 UFC
       Delta = +1.00 (Avantage Dricus Du Plessis)
=================================================================
```
