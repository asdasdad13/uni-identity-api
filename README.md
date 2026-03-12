To start virtual environment:

`.venv/Scripts/activate`

To deactivate virtual environment:

`deactivate`

# 2. Generate RSA Keys for OIDC
Before running the application, generate RSA key pairs:
## Generate private key
```
openssl genrsa -out oidc_private.key 2048
```

## Generate public key from private key
```
openssl rsa -in oidc_private.key -pubout -out oidc_public.key
```

# 3. Install Dependencies
```
pip install -r requirements.txt
```

# 4. Run Migrations
To make migrations and migrate:

```
python manage.py migrate
```

# 5. Run Server
To run the server:
```
python manage.py runserver
```

To run tests:
```
python manage.py test
```