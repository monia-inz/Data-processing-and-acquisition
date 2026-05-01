# Datalogger IoT – Monitoring de centrale photovoltaïque
### Projet de stage | Surveillance à distance d'installations photovoltaïques

---

## Description

Ce projet a pour objectif de concevoir et développer un **datalogger IoT** capable de collecter,
traiter et transmettre les données d'une installation photovoltaïque à distance.

Il permet d'assurer la **télésurveillance** des centrales solaires en mesurant en temps réel :
- La **puissance** produite
- La **tension alternative** (AC)
- Le **courant alternatif** (AC)
- La **fréquence** du réseau

Le système s'inscrit dans une approche **IoT (Internet of Things)** pour couvrir une large zone
de maintenance à distance, en offissant rapidité, clarté et fiabilité des données.

---

## Architecture du système
Panneaux solaires (DC)
│
▼
Onduleurs (DC → AC)
│
├──────────────────────► Tableau électrique → Compteur → Réseau haute tension
│                                          └──► Autoconsommation sur place
│
▼
Datalogger (collecte des données)
│
▼
Serveur FTP / EPICE / MONITORING
---

## Stack technique

| Couche       | Technologie          |
|--------------|----------------------|
| **Firmware** | C (microcontrôleur)  |
| **Backend**  | Python               |
| **Protocol** | Communication onduleur ↔ panneau PV |
| **Hardware** | Datalogger (ex: WEBDYN Sun) |
| **Serveur**  | FTP / EPICE / Monitoring |

---

## Fonctionnalités

- Collecte automatique des mesures de l'installation photovoltaïque
- Transmission des données vers un serveur distant (FTP / monitoring)
- Surveillance en temps réel : puissance, tension, courant, fréquence
- Architecture modulaire : partie **hardware** + partie **software** indépendantes
- Compatible avec les onduleurs des centrales clients (société EMASOLAR)

---

## Structure du projet
/
├── firmware/         # Code C embarqué (microcontrôleur / datalogger)
│   ├── src/
│   └── include/
├── software/         # Scripts Python (collecte, traitement, envoi)
│   ├── datalogger.py
│   ├── communication.py
│   └── monitoring.py
├── docs/             # Documentation technique et rapports de stage
├── schemas/          # Schémas d'architecture et synoptiques
└── README.md
---

## Prérequis

### Python
```bash
python >= 3.8
pip install -r requirements.txt
```

### C (Firmware)
- Compilateur : GCC ou compilateur spécifique au microcontrôleur cible
- Environnement : MPLAB / STM32CubeIDE (selon le matériel)

---

## Installation & Lancement

```bash
# Cloner le dépôt
git clone https://github.com/votre-repo/datalogger-pv.git
cd datalogger-pv

# Installer les dépendances Python
pip install -r requirements.txt

# Lancer le monitoring
python software/datalogger.py
```

---

## Références matérielles

- **Datalogger** : WEBDYN Sun (déployé sur les centrales EMASOLAR)
- **Onduleurs** : compatibles protocole de communication étudié dans le projet
- **Serveur** : FTP / EPICE / plateforme de monitoring

---

## Auteur

Projet de stage – Société EMASOLAR  
Étude et développement d'un système de monitoring IoT pour centrales photovoltaïques
