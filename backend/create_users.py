import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurement.settings')

import django
django.setup()

from apps.users.models import User

data = [
    ('admin@acme.com', 'Sophie Martin', 'ADMIN'),
    ('demandeur@acme.com', 'Karim Benali', 'DEMANDEUR'),
    ('validateur@acme.com', 'Anne Dupont', 'VALIDATEUR'),
    ('acheteur@acme.com', 'Marc Lefevre', 'ACHETEUR'),
    ('magasinier@acme.com', 'Yasmine Haddad', 'MAGASINIER'),
    ('direction@acme.com', 'Pierre Rousseau', 'DIRECTION'),
]

for email, name, role in data:
    User.objects.create_user(email=email, password='demo1234', full_name=name, role=role)
    print(f'Cree: {email}')

print('Termine !')