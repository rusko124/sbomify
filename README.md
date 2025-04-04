# sbomify

sbomify is a Software Bill of Materials (SBOM) management platform that can be self-hosted or accessed through [app.sbomify.com](https://app.sbomify.com). The platform provides a centralized location to upload and manage your SBOMs, allowing you to share them with stakeholders or make them publicly accessible.

The sbomify backend integrates with our [github actions module](https://github.com/sbomify/github-action) to automatically generate SBOMs from lock files and docker files.

For more information, see [sbomify.com](https://sbomify.com).

## Roadmap and Goals

* Be compatible with both CycloneDX and SPDX SBOM formats
* Be compatible with Project Koala / [Transparency Exchange API (TEA)](https://github.com/CycloneDX/transparency-exchange-api/)

## Releases

For information about cutting new releases, see [RELEASE.md](docs/RELEASE.md).

## Deployment

The application is automatically deployed to [fly.io](https://fly.io) when changes are pushed to the `master` branch (staging) or when a new version tag is created (production).

For detailed information about the deployment process, including:

* CI/CD workflow
* Fly.io configuration
* Environment setup
* Storage configuration

See [docs/deployment.md](docs/deployment.md).

## Local Development

### Authentication During Development

For local development, authentication is handled through Django's admin interface:

```bash
# Create a superuser for local development
docker compose \
    -f docker-compose.yml \
    -f docker-compose.dev.yml exec \
    sbomify-backend \
    poetry run python manage.py createsuperuser
```

Then access the admin interface at `http://localhost:8000/admin` to log in.

> **Note**: Production environments use different authentication methods. See [docs/deployment.md](docs/deployment.md) for production authentication setup.

### Development Prerequisites

* Python 3.12+
* Poetry
* Docker (for running PostgreSQL and Minio)
* Bun (for JavaScript development)

### API Documentation

The API documentation is available at:

* Interactive API docs (Swagger UI): `http://localhost:8000/api/v1/docs`
* OpenAPI specification: `http://localhost:8000/api/v1/openapi.json`

These endpoints are available when running the development server.

### Setup

1. Copy `.env.example` to `.env` and adjust values as needed:

```bash
cp .env.example .env
```

2. Start the development environment (recommended method):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

3. Create a local admin account:

```bash
docker compose \
    -f docker-compose.yml \
    -f docker-compose.dev.yml exec \
    -e DJANGO_SUPERUSER_USERNAME=sbomifyadmin \
    -e DJANGO_SUPERUSER_PASSWORD=sbomifyadmin \
    -e DJANGO_SUPERUSER_EMAIL=admin@sbomify.com \
    sbomify-backend \
    poetry run python manage.py createsuperuser --noinput
```

4. Access the application:
   * Admin interface: `http://localhost:8000/admin`
   * Main application: `http://localhost:8000`

> **Note**: For production deployment information, see [docs/deployment.md](docs/deployment.md).

#### Alternative: Running Locally (without Docker for Django)

* Start required services in Docker:

```bash
# Start both PostgreSQL and MinIO
docker compose up sbomify-db sbomify-minio sbomify-createbuckets -d
```

* Install dependencies:

```bash
poetry install
bun install  # for JavaScript dependencies
```

* Run migrations:

```bash
poetry run python manage.py migrate
```

* Start the development servers:

```bash
# In one terminal, start Django
poetry run python manage.py runserver

# In another terminal, start Vite
bun run dev
```

### Configuration

#### Development Server Settings

The application uses Vite for JavaScript development. The following environment
variables control the development servers:

```bash
# Vite development settings
DJANGO_VITE_DEV_MODE=True
DJANGO_VITE_DEV_SERVER_PORT=5170
DJANGO_VITE_DEV_SERVER_HOST=http://localhost

# Static and development server settings
STATIC_URL=/static/
DEV_JS_SERVER=http://127.0.0.1:5170
WEBSITE_BASE_URL=http://127.0.0.1:8000
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_WEBSITE_BASE_URL=http://127.0.0.1:8000
```

These settings are preconfigured in the `.env.example` file.

#### S3/Minio Storage

The application uses S3-compatible storage for storing files and assets. In
development, we use Minio as a local S3 replacement.

* When running with Docker Compose, everything is configured automatically
* When running locally (Django outside Docker):
  * Make sure Minio is running via Docker:
     `docker compose up sbomify-minio sbomify-createbuckets -d`
  * Set `AWS_S3_ENDPOINT_URL=http://localhost:9000` in your `.env`
  * The required buckets (`sbomify-media` and `sbomify-sboms`) will be created
     automatically

You can access the Minio console at:

* `http://localhost:9001`
* Default credentials: minioadmin/minioadmin

### Running test cases

```bash
poetry run coverage run -m pytest --pdb -x -s
poetry run coverage report
```

### JS build tooling

For frontend JS work, setting up JS tooling is required.

#### Bun

```bash
curl -fsSL https://bun.sh/install | bash
```

In the project folder at the same level as `package.json`:

```bash
bun install
```

#### Linting

For JavaScript/TypeScript linting:

```bash
# Check for linting issues (used in CI and can be run locally)
bun lint

# Fix linting issues automatically (local development only)
bun lint-fix
```

#### Run vite dev server

```bash
bun run dev
```

## Production Deployment

### Production Prerequisites

* Docker and Docker Compose
* S3-compatible storage (like MinIO)
* PostgreSQL database
* Auth0 account for authentication (Note: Migration to Keycloak is planned)
* Reverse proxy (e.g., Nginx) for production deployments

### Docker Compose Configuration

The application uses two Docker Compose files:

* `docker-compose.yml`: Base configuration with development defaults
* `docker-compose.prod.yml`: Production overrides that:
  * Remove development-specific settings
  * Add production-specific configurations
  * Configure proper restart policies
  * Remove exposed ports except for the web interface
  * Remove development volume mounts

### Reverse Proxy Setup

For production deployments, it's strongly recommended to put a reverse proxy (such as Nginx) in front of the application server. This provides:

* SSL/TLS termination
* Better security
* Static file serving
* Load balancing (if needed)
* Request buffering
* Gzip compression

### Authentication

#### Current: Auth0 Configuration

> **Important Migration Notice**: We are in the process of migrating from Auth0 to Keycloak for authentication. This work is being tracked in [issue #1](https://github.com/sbomify/sbomify/issues/1). During this transition period, you can:
>
> * Continue using Auth0 configuration as described below
> * Use Django admin interface (/admin) with local users for development
> * Follow the migration issue for updates

Create a "Regular Web Application" in Auth0 with the following settings:

| Setting | Value |
|---------|-------|
| APPLICATION LOGIN URI | https://[yourdomain] |
| ALLOWED CALLBACK URLs | https://[yourdomain]/complete/auth0 |
| ALLOWED LOGOUT URLs | https://[yourdomain] |
| ALLOWED WEB ORIGINS | https://[yourdomain] |

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
POSTGRES_PASSWORD=<secure-password>

# Security
SECRET_KEY=<django-secret-key>

# Auth0
SOCIAL_AUTH_AUTH0_DOMAIN=<your-auth0-domain>
SOCIAL_AUTH_AUTH0_KEY=<your-auth0-client-id>
SOCIAL_AUTH_AUTH0_SECRET=<your-auth0-client-secret>

# Storage (MinIO/S3)
AWS_ACCESS_KEY_ID=<your-s3-access-key>
AWS_SECRET_ACCESS_KEY=<your-s3-secret-key>

# Application
APP_BASE_URL=https://[your-domain]
```

To disable billing, use `BILLING=False`.

Before you begin, you need a [create webhook](https://dashboard.stripe.com/workbench/webhooks/create) and point it to `https://[your-domain]/webhook/`.

```bash
# Billing
STRIPE_BILLING_URL=https://billing.stripe.com/p/login/[redacted]
STRIPE_PUBLISHABLE_KEY=[redacted]
STRIPE_SECRET_KEY=[redacted]
STRIPE_WEBHOOK_SECRET=
```

### Running in Production

1. Build and start the production stack:

```bash
# Build the images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start the stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

1. Create a superuser account (first time only):

```bash
docker compose exec sbomify-backend poetry run python manage.py createsuperuser
```

1. The application will be available at `http://[your-domain]:8000`

### SBOM Upload via API

#### CycloneDX

```shell
curl -v -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  --data-binary @cyclonedx-format-sbom-file.json \
  https://[your-domain]/api/v1/sboms/artifact/cyclonedx/<component-id>
```

#### SPDX

```shell
curl -v -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  --data-binary @spdx-format-sbom-file.json \
  https://[your-domain]/api/v1/sboms/artifact/spdx/<component-id>
```

### Backup and Restore

```shell
# Take DB backup
docker compose exec sbomify-db pg_dump -U sbomify sbomify > backup.sql

# Restore DB from backup
cat backup.sql | docker compose exec -T sbomify-db psql -U sbomify sbomify
```

### Generating Pydantic Models

For sbom formats, models for new versions can be generated using
`datamodel-codegen` which is installed as a dev dependency.

```shell
poetry run datamodel-codegen \
  --url https://github.com/CycloneDX/specification/raw/refs/tags/1.6/schema/bom-1.6.schema.json \
  --output-model-type pydantic_v2.BaseModel \
  --use-standard-collections \
  --use-subclass-enum \
  --use-double-quotes \
  --use-schema-description \
  --target-python-version 3.10 \
  --use-annotated \
  --output cyclonedx
```
