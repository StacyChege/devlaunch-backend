# Deploying DevLaunch (GHCR + Dokploy)

Two repos, one Dokploy compose service. Each repo builds its own image on
push to `main`; both then trigger the **same** compose redeploy.

```
push devlaunch-backend  → GH Actions builds ghcr.io/stacychege/devlaunch-backend  → redeploy
push devlaunch-frontend → GH Actions builds ghcr.io/stacychege/devlaunch-frontend → redeploy
Dokploy pulls both :latest images and recreates the containers
```

## What's already in the repos

| File | Repo |
|---|---|
| `Dockerfile`, `entrypoint.sh`, `requirements.txt` | backend |
| `docker-compose.yml` | backend (Dokploy points here) |
| `.github/workflows/build.yml` | both |
| `Dockerfile`, `nginx.conf` | frontend |

## Manual steps (yours)

### 1. GHCR package visibility
After the first successful Actions run, open each package on GitHub and set
**Package settings → Change visibility → Public** (or authenticate Docker on
the Dokploy host).

### 2. Dokploy — create the Compose service
- **Compose → Create Compose**
- **Provider → GitHub App →** repo `devlaunch-backend`, branch `main`,
  file `./docker-compose.yml`
- **General tab → Autodeploy OFF** (critical — the workflow handles timing)
- **Environment tab →** set every `${VAR}` from `docker-compose.yml`
  (`SECRET_KEY`, `ALLOWED_HOSTS`, `DB_*`, `CORS_ALLOWED_ORIGINS`,
  `FRONTEND_URL`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `STRIPE_SECRET_KEY`,
  `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`)
- **backend service → Domains →** `api.<your-domain>` → port `8000`
- **frontend service → Domains →** `<your-domain>` → port `80`

### 3. GitHub secrets — add to **both** repos
`Settings → Secrets and variables → Actions`

| Secret | Value |
|---|---|
| `DOKPLOY_URL` | e.g. `https://dokploy.example.com` |
| `DOKPLOY_API_KEY` | Dokploy → Settings → Profile → API → generate (no expiry) |
| `DOKPLOY_COMPOSE_ID` | last segment of the compose service's URL in Dokploy |
| `VITE_API_BASE_URL` | **frontend repo only** — e.g. `https://api.<your-domain>/api` |

### 4. Database
`docker-compose.yml` expects MySQL reachable from the container. For a
host-installed MySQL set `DB_HOST=host.docker.internal`; for a managed DB
use its host. The container runs `migrate` on every start.

### 5. First deploy
Push to `main` (or run the workflow manually) → watch Actions (~3–6 min) →
Dokploy log should show `Container devlaunch-backend Recreate`, not just
`Running`. Then create the admin user from the Dokploy service terminal:

```
python manage.py createsuperuser
python manage.py seed_templates
```

See `DEPLOY_TEMPLATE.md` for the full reference and Traefik gotchas.
