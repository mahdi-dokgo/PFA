# Procurement Backend — Django REST Framework

Backend complet pour le système de gestion des achats et approvisionnements.
Correspond exactement au contrat API de `approvewise-gateway` (Lovable frontend).

---

## ⚡ Installation rapide

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer la base de données PostgreSQL
createdb procurement_db

# 4. Appliquer les migrations
python manage.py makemigrations users suppliers articles requests_app consultations orders receptions stock
python manage.py migrate

# 5. Créer un superadmin
python manage.py createsuperuser

# 6. Lancer le serveur
python manage.py runserver
```

L'API sera disponible sur `http://localhost:8000/api/`

---

## 🔌 Connexion avec le frontend Lovable

Dans le fichier `.env` du projet Lovable (approvewise-gateway) :
```
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 🗂️ Structure des apps

| App | Endpoints |
|-----|-----------|
| `apps/users` | `/api/auth/`, `/api/users/` |
| `apps/suppliers` | `/api/suppliers/` |
| `apps/articles` | `/api/articles/`, `/api/categories/` |
| `apps/requests_app` | `/api/purchase-requests/` |
| `apps/consultations` | `/api/consultations/` |
| `apps/orders` | `/api/purchase-orders/` |
| `apps/receptions` | `/api/receptions/` |
| `apps/stock` | `/api/stock/movements/`, `/api/stock/alerts/` |
| `apps/dashboard` | `/api/dashboard/kpis/` etc. |

---

## 🔐 Authentification

JWT via `djangorestframework-simplejwt`.

Login → `POST /api/auth/login/` → retourne `{ token, user }`

Ajouter dans les headers : `Authorization: Bearer <token>`

---

## 📋 Comptes de démo à créer

Créez ces utilisateurs via `python manage.py shell` :

```python
from apps.users.models import User
users = [
    ('admin@acme.com', 'Admin User', 'ADMIN'),
    ('demandeur@acme.com', 'Karim Benali', 'DEMANDEUR'),
    ('validateur@acme.com', 'Sara Idrissi', 'VALIDATEUR'),
    ('acheteur@acme.com', 'Youssef Alami', 'ACHETEUR'),
    ('magasinier@acme.com', 'Hassan Tazi', 'MAGASINIER'),
    ('direction@acme.com', 'Pierre Rousseau', 'DIRECTION'),
]
for email, name, role in users:
    User.objects.create_user(email=email, password='demo1234', full_name=name, role=role)
print("✅ Utilisateurs créés")
```
