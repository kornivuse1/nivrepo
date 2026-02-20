# NivPro – VPS deployment (step-by-step)

This guide walks you through: buying a VPS, pushing code to GitHub, using CI to build the Docker image, and running the app on the VPS with Docker Compose and Nginx.

---

## Phase 1: Get a VPS and a domain (optional)

### Step 1.1 – Choose a provider and create a server

- **Providers**: DigitalOcean, Linode, Vultr, Hetzner, or any VPS provider.
- **Create a droplet/instance**:
  - **OS**: Ubuntu 22.04 LTS (recommended).
  - **Size**: Small (1 CPU, 1 GB RAM) is enough to start.
  - **Region**: Pick one close to you or your users.
- Note the **server IP** (e.g. `165.232.123.45`) and that you can log in as **root** (or with a user + sudo) via SSH.

### Step 1.2 – (Optional) Point a domain to the server

- If you have a domain (e.g. `music.yourdomain.com`), add an **A record** pointing to the VPS IP.
- If you skip this, you will use the IP only (e.g. `http://165.232.123.45`). You can add a domain later.

---

## Phase 2: First login and basic server setup

### Step 2.1 – Connect via SSH

On your laptop (PowerShell or terminal):

```bash
ssh root@YOUR_VPS_IP
```

(Replace `YOUR_VPS_IP` with your real IP. If you use a key file: `ssh -i path\to\key root@YOUR_VPS_IP`.)

### Step 2.2 – Create a non-root user (recommended)

```bash
adduser nivpro
usermod -aG sudo nivpro
```

Log out and log in as `nivpro`, then use `sudo` for admin commands:

```bash
ssh nivpro@YOUR_VPS_IP
```

### Step 2.3 – Update the system and open firewall

```bash
sudo apt update && sudo apt upgrade -y
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

(22 = SSH, 80 = HTTP, 443 = HTTPS.)

---

## Phase 3: Install Docker and Docker Compose on the VPS

### Step 3.1 – Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

Log out and log in again so the `docker` group applies (or run `newgrp docker`).

### Step 3.2 – Install Docker Compose (plugin)

```bash
sudo apt install -y docker-compose-plugin
```

Check:

```bash
docker --version
docker compose version
```

---

## Phase 4: Push your project to GitHub and set up CI

### Step 4.1 – Create a GitHub repo and push code

1. On GitHub: **New repository** (e.g. `nivpro`). Do **not** add a README if your folder already has one.
2. On your laptop, in the project folder:

```bash
cd c:\Users\korni\NivPro
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nivpro.git
git push -u origin main
```

(Replace `YOUR_USERNAME` and `nivpro` with your GitHub username and repo name.)

### Step 4.2 – Make the GitHub package public (so the VPS can pull without auth)

1. GitHub → your repo → **Packages** (right side), or go to `https://github.com/YOUR_USERNAME/nivpro/pkgs/container/nivpro`.
2. **Package settings** → **Change visibility** → **Public**.

(If you prefer to keep it private, you will configure the VPS to log in to GHCR with a token; we can add that later.)

### Step 4.3 – Add secrets for deployment (optional: deploy from CI)

If you want GitHub Actions to deploy to the VPS on every push to `main`:

1. On the VPS, create an SSH key for the deploy user:

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
```

2. Copy the **private** key (you will paste it in GitHub):

```bash
cat ~/.ssh/github_deploy
```

Copy the whole output (including `-----BEGIN ... END ...`).

3. In GitHub: repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Name            | Value                    |
|-----------------|--------------------------|
| `VPS_HOST`      | Your VPS IP              |
| `VPS_USER`      | `nivpro` (or `root`)     |
| `SSH_PRIVATE_KEY` | The pasted private key |

---

## Phase 5: Add the deploy job to CI and production files

You need three things in the repo:

1. **Deploy job** in the GitHub Actions workflow (SSH to VPS and run `docker compose pull && up`).
2. **Production `docker-compose`** on the VPS that pulls the image from GHCR (no build on server).
3. **Nginx** in front of the app (and optionally HTTPS).

We'll add the workflow deploy step and example configs next.

### Step 5.1 – Deploy workflow (add to `.github/workflows/ci.yml`)

After the `build` job, add a **deploy** job that runs only on push to `main` and only if the three secrets exist. Example:

```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/nivpro
            docker compose pull
            docker compose up -d
```

This expects the app to live in `~/nivpro` on the VPS and use a `docker-compose` that pulls the image (see Step 6).

### Step 5.2 – One-time setup on the VPS: app directory and env

On the VPS, create the app directory and copy the production config from your repo. Either clone the repo once and use the `deploy/` folder, or create the files by hand:

**Option A – Clone repo and copy deploy files**

```bash
git clone https://github.com/YOUR_USERNAME/nivpro.git ~/nivpro-repo
mkdir -p ~/nivpro
cp ~/nivpro-repo/deploy/docker-compose.prod.yml ~/nivpro/
cp ~/nivpro-repo/deploy/nginx.conf ~/nivpro/
```

Then edit `~/nivpro/docker-compose.prod.yml` and replace `YOUR_GITHUB_USERNAME` with your GitHub username (lowercase).

**Option B – Create directory and files by hand**

```bash
mkdir -p ~/nivpro
cd ~/nivpro
```

Create `.env` (see below), then create `docker-compose.prod.yml` and `nginx.conf` with the contents from the repo’s `deploy/` folder (see [deploy/docker-compose.prod.yml](deploy/docker-compose.prod.yml) and [deploy/nginx.conf](deploy/nginx.conf)).

Create the env file:

```bash
nano .env
```

In `.env` (replace with a strong secret and your GitHub details if needed):

```env
SECRET_KEY=generate-a-long-random-string-here
DATABASE_URL=sqlite+aiosqlite:////data/nivpro.db
UPLOAD_DIR=/data/uploads
```

Generate a secret (on your laptop or VPS):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Save and exit (Ctrl+O, Enter, Ctrl+X in nano).

---

## Phase 6: Production Docker Compose and Nginx on the VPS

On the VPS you will use a **production** compose file that **pulls** the image from GitHub (no build). Nginx will sit in front and forward to the app.

### Step 6.1 – Production compose and Nginx on the VPS

If you used **Option A** in Step 5.2, you already have `docker-compose.prod.yml` and `nginx.conf` in `~/nivpro`. Just ensure the image name in `docker-compose.prod.yml` is correct: `ghcr.io/YOUR_GITHUB_USERNAME/nivpro:latest` (lowercase username).

If you created files by hand, use the contents from the repo’s **deploy/** folder:

- [deploy/docker-compose.prod.yml](deploy/docker-compose.prod.yml) – replace `YOUR_GITHUB_USERNAME`
- [deploy/nginx.conf](deploy/nginx.conf)

### Step 6.2 – First run on the VPS

```bash
cd ~/nivpro
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Open in the browser: `http://YOUR_VPS_IP`. You should see the NivPro login.

To use the **deploy** job from CI, the script on the VPS must use this file and directory. For example, in the workflow use:

```yaml
script: |
  cd ~/nivpro
  docker compose -f docker-compose.prod.yml pull
  docker compose -f docker-compose.prod.yml up -d
```

---

## Phase 7: (Optional) HTTPS with Let's Encrypt

If you have a domain (e.g. `music.yourdomain.com`) pointing to the VPS:

### Step 7.1 – Install Certbot on the VPS

```bash
sudo apt install -y certbot
```

### Step 7.2 – Get a certificate

Temporarily stop Nginx so Certbot can use port 80:

```bash
cd ~/nivpro
docker compose -f docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d music.yourdomain.com
```

### Step 7.3 – Update Nginx to use HTTPS

Edit `nginx.conf`:

```nginx
server {
    listen 80;
    server_name music.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name music.yourdomain.com;
    client_max_body_size 50M;

    ssl_certificate     /etc/letsencrypt/live/music.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/music.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Update `docker-compose.prod.yml` so Nginx mounts the certs:

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - app
    restart: unless-stopped
```

Restart:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Renew certs (e.g. cron):

```bash
sudo certbot renew
```

---

## Phase 8: Deploy job in the repo

The repo already includes a **deploy** job in `.github/workflows/ci.yml`. It runs only when the three secrets are set: `VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`. Until you add them and complete the VPS setup (Phases 1–6), the deploy step will fail; that is expected.

After you add the secrets and have `~/nivpro` with `docker-compose.prod.yml` and `.env` on the VPS, the next push to `main` will:

1. Run tests  
2. Build the Docker image and push to GHCR  
3. SSH to the VPS and run `docker compose -f docker-compose.prod.yml pull && up -d`

---

## Quick reference

| Step | Where | What |
|------|--------|------|
| 1 | Provider | Create VPS (Ubuntu 22.04), note IP |
| 2 | VPS | SSH, optional user, `ufw` (22, 80, 443) |
| 3 | VPS | Install Docker + Docker Compose plugin |
| 4 | Laptop + GitHub | Push repo, set package public, add VPS secrets |
| 5 | Repo + VPS | Add deploy job in CI; create `~/nivpro`, `.env` on VPS |
| 6 | VPS | Add `docker-compose.prod.yml` and `nginx.conf`, run compose |
| 7 | VPS (optional) | Certbot + Nginx HTTPS |
| 8 | Repo | Ensure deploy job uses correct path and compose file |

---

*For app features and development, see [README.md](README.md) and [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md).*
