To start virtual environment:

`.venv/Scripts/activate`

To deactivate virtual environment:

`deactivate`

# Generate RSA Keys for OIDC
Before running the application, generate RSA key pairs:
## Private key
```
openssl genrsa -out oidc_private.key 2048
```

## Public key from private key
```
openssl rsa -in oidc_private.key -pubout -out oidc_public.key
```

# Install dependencies
```
pip install -r requirements.txt
```

# Run server
```
python manage.py runserver
```

# Run migrations
To make migrations and migrate:

```
python manage.py makemigrations
python manage.py migrate
```

## Flush database
```
python manage.py flush
```

## Seed the database with dummy data
Database in source code is already seeded, but you may seed again if you happened to flush it.
```
python manage.py seed
python manage.py setup_oidc_apps
```

# Run unit tests:
```
python manage.py test
```