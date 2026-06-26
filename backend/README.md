# ApprovWise — Système web de gestion des achats et approvisionnements

Application web développée dans le cadre du **Projet de Fin d'Année (PFA)** — EMSI Rabat, filière 3IIR (2025–2026).

**Réalisé par :** LAMLIHE Mohamed AlMahdi & AGRA Youssef
**Encadrante :** Mme Houda Orchi

---

## Présentation

ApprovWise est une application web métier couvrant l'intégralité du cycle **procure-to-pay** d'une organisation :

- Demandes d'achat avec workflow de validation (Brouillon → Soumise → Validée/Rejetée → Convertie)
- Consultations multi-fournisseurs avec comparaison des offres
- Bons de commande avec numérotation automatique et export PDF
- Réceptions de marchandises (totales et partielles)
- Vérification des factures par rapprochement à trois voies (BC / Réception / Facture)
- Gestion des stocks avec alertes de réapprovisionnement
- Journal d'audit global et tableau de bord analytique par rôle

L'application implémente un contrôle d'accès basé sur les rôles (**RBAC**) avec six profils : Administrateur, Demandeur, Validateur, Acheteur, Magasinier et Direction.

---

## Stack technique

| Couche          | Technologie                  |
|-----------------|------------------------------|
| Backend         | Python 3.11, Django 5.0.6    |
| Frontend        | Bootstrap 5, Chart.js        |
| Base de données | MySQL 8                      |
| Architecture    | MVT (Modèle-Vue-Template)    |
| Export PDF      | ReportLab                    |
| Export Excel    | OpenPyXL                     |

---

## Installation

### Prérequis

- Python 3.11+
- MySQL 8
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone <url-du-repo>
cd backend

# 2. Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Modifier .env avec vos paramètres MySQL (DB_NAME, DB_USER, DB_PASSWORD)

# 5. Créer la base de données MySQL
mysql -u root -p -e "CREATE DATABASE procurement_db CHARACTER SET utf8mb4;"

# 6. Appliquer les migrations
python manage.py migrate

# 7. Charger les données de démonstration (Clinique Al Shifa)
python manage.py reseed_demo

# 8. Lancer le serveur
python manage.py runserver
```

L'application est accessible sur **http://localhost:8000**

---

## Comptes de démonstration — Clinique Al Shifa

| Rôle           | Email                        | Mot de passe | Nom                |
|----------------|------------------------------|--------------|--------------------|
| Administrateur | k.benali@alshifa.ma          | admin        | Karim Benali       |
| Demandeur      | n.ezzahraoui@alshifa.ma      | 1234         | Nadia Ezzahraoui   |
| Validateur     | m.tazi@alshifa.ma            | 1234         | Mourad Tazi        |
| Acheteur       | s.idrissi@alshifa.ma         | 1234         | Salma Idrissi      |
| Magasinier     | h.ouchen@alshifa.ma          | 1234         | Hassan Ouchen      |
| Direction      | y.amrani@alshifa.ma          | 1234         | Dr. Youssef Amrani |

> **Important :** Ces mots de passe sont destinés uniquement à la démonstration locale. Ils doivent être modifiés avant tout déploiement en production.

---

## Structure du projet
backend/

├── procurement/          # Configuration Django (settings, urls, wsgi)

├── apps/

│   ├── users/            # Modèle utilisateur personnalisé, 6 rôles

│   ├── suppliers/        # Fournisseurs, archivage logique

│   ├── articles/         # Articles, catégories, association fournisseurs (M2M)

│   ├── requests_app/     # Demandes d'achat, lignes DA, historique

│   ├── consultations/    # Consultations, propositions fournisseurs

│   ├── orders/           # Bons de commande, lignes BC

│   ├── receptions/       # Réceptions, lignes de réception

│   ├── stock/            # Mouvements de stock, ajustements

│   ├── factures/         # Factures fournisseurs, 3-way matching

│   ├── notifications/    # Notifications in-app, signaux Django

│   ├── audit/            # Journal d'audit global

│   ├── dashboard/        # API KPIs du tableau de bord

│   ├── webapp/           # Frontend Django (vues, formulaires, templates)

│   └── common/           # Mixins et utilitaires partagés

├── templates/            # Templates HTML (Bootstrap 5)

├── static/               # Fichiers statiques (CSS, JS, images)

├── requirements.txt

└── manage.py

---

## Commandes utiles

```bash
# Recharger les données de démonstration
python manage.py reseed_demo

# Créer un superutilisateur
python manage.py createsuperuser

# Accéder à l'interface d'administration Django
# → http://localhost:8000/admin/
```

---

## Jeu de données de démonstration

La commande `reseed_demo` crée un scénario complet pour la **Clinique Al Shifa** (Rabat) :

- 6 utilisateurs avec rôles distincts
- 5 fournisseurs spécialisés (médicaments, équipements, hygiène, bureau, informatique)
- 10 articles répartis en 4 catégories
- 6 demandes d'achat couvrant tous les statuts du workflow
- 4 bons de commande à différents stades
- Réceptions, factures, consultation et entrées d'audit

---

## Licence

Projet académique — EMSI Rabat, PFA 2025–2026.
