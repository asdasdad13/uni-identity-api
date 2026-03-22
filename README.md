Getting Started
# 1. Environment Setup
Create and activate a virtual environment.

Windows:
```
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

# 2. Dependency Installation
```
pip install -r requirements.txt
```

# 3. Security: RSA Key Generation
The OIDC provider requires an RSA key pair for token signing. Generate these in the project root:
```
# Generate Private key
openssl genrsa -out oidc_private.key 2048

# Generate Public key
openssl rsa -in oidc_private.key -pubout -out oidc_public.key
```

# 4. Initialise database
Initialize the database and prepare the OIDC application registry.

# 5. Run the application
```
python manage.py runserver
```

# Testing & Documentation
- **Unit Tests**: Run `python manage.py test`.
- **API Documentation**: Once the server is running, visit /api/docs/ for the Swagger UI, get a JWT from /api/token/, and authorise at the top right of the view.
