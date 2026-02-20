# NivPro – Project Summary

A summary of the work done on the NivPro music player server from initial setup through current features.

---

## 1. Project goal

- **24/7 music server** for personal/family use.
- **You (and admins)** upload and manage songs via a separate admin UI.
- **Family and friends (viewers)** log in to search and play songs only.
- **Deployment**: Run locally first; later deploy to a VPS with Docker and CI.

---

## 2. Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.12, FastAPI |
| Database | SQLite (async via aiosqlite); design allows PostgreSQL via `DATABASE_URL` |
| Auth | JWT (python-jose), bcrypt for passwords |
| Frontend | Jinja2 templates, vanilla JS, CSS |
| Storage | Song files and background images on disk; metadata in DB |
| Deploy | Docker, docker-compose, GitHub Actions (test, build image, push to GHCR) |

---

## 3. Architecture (high level)

- **Single codebase**, one server process.
- **Player** at `/` – for viewers (and admins when they want to listen).
- **Admin** at `/admin` – for admins only (upload, delete, edit songs; manage users and settings).
- **Roles**: `viewer` (play, search, love songs) and `admin` (full management + play).
- **Data**: Metadata in SQLite; audio files in `uploads/`; background images in `uploads/images/`.

---

## 4. Implemented features

### 4.1 Authentication and users

- Login with username/password; JWT stored in `localStorage` (separate keys for player and admin).
- **Viewers**: Can list songs, search, stream, love songs.
- **Admins**: Can do everything viewers can, plus manage songs, backgrounds, users, and settings.
- First run: if no users exist, a default **admin** user is created (username: `admin`, password: `admin`).
- Optional script: `python -m app.scripts.create_admin` to create more users (admin or viewer).

### 4.2 Player page (`/`)

- **Unified player bar**: Previous, Play/Pause, Next, Shuffle, current song title/artist, Love.
- **Playlist behavior**: Songs play one after another; shuffle toggles random order.
- **Search**: Filter song list by title/artist.
- **Love**: Heart icon (♡/❤); users can love/unlove the current song; count shown per song.
- **Background**: Optional background image (one active at a time); optional “auto-change background when song changes” (random image per song).
- **Streaming**: Audio is fetched with auth and played via a blob URL (no native `<audio src>` to avoid missing `Authorization` header).

### 4.3 Admin page (`/admin`)

- **Songs**: Upload (mp3, m4a, ogg, wav, flac), edit title/artist, delete, **play** (mini player bar with Play/Pause and “Now playing”).
- **Love counts**: Each song shows how many users loved it (❤ N).
- **Background images**: Upload (jpg, png, gif, webp), activate one as player background, delete.
- **Setting**: “Auto-change background when song changes” (on/off).
- **Users / listeners**: List all users; remove a user (revokes access); cannot remove yourself.

### 4.4 Data and storage

- **Songs**: Metadata in `songs` table (id, filename, title, artist, duration_seconds, created_at); files in `UPLOAD_DIR` (e.g. `uploads/`). Metadata can be read from file tags (mutagen).
- **Background images**: `background_images` table; files in `uploads/images/`; one row can be marked `is_active`.
- **Users**: `users` table (username, password_hash, role, created_at).
- **Loves**: `song_loves` table (user_id, song_id, created_at) with unique (user_id, song_id).
- **App settings**: `app_settings` table (e.g. `auto_change_background`).

---

## 5. Project structure (main pieces)

```
NivPro/
├── .github/workflows/ci.yml    # Test, build Docker image, push to GHCR
├── app/
│   ├── main.py                 # FastAPI app, lifespan, routes for / and /admin
│   ├── config.py               # Settings (SECRET_KEY, DATABASE_URL, UPLOAD_DIR, etc.)
│   ├── auth.py                 # JWT, password hash/verify, get_current_user, get_current_admin
│   ├── database.py             # Async SQLite engine, session, init_db, get_db
│   ├── models/
│   │   ├── user.py             # User, UserRole (viewer, admin)
│   │   ├── song.py             # Song
│   │   ├── background_image.py # BackgroundImage
│   │   ├── settings.py        # AppSettings
│   │   └── song_love.py       # SongLove
│   ├── routers/
│   │   ├── auth_router.py     # POST /api/auth/login, GET /api/auth/me
│   │   ├── player.py          # Songs list/stream, background, love, settings
│   │   ├── admin.py           # Admin songs CRUD + love_count
│   │   ├── background.py      # Admin backgrounds CRUD, activate
│   │   ├── users.py           # Admin list/delete users
│   │   └── settings.py        # Admin get/patch app settings
│   ├── services/song_service.py  # Song create, list, delete, metadata (mutagen)
│   ├── static/
│   │   ├── style.css          # Shared + player + admin styles
│   │   ├── player.js          # Player UI, playlist, shuffle, love, background
│   │   └── admin.js           # Admin UI, play in admin, settings, users
│   └── scripts/create_admin.py   # CLI to create admin (or viewer) user
├── templates/
│   ├── base.html
│   ├── player.html            # Player page
│   └── admin.html             # Admin page
├── uploads/                   # Song files (gitignored; volume in Docker)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 6. API overview (concise)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | - | Login (form: username, password); returns JWT |
| GET | `/api/auth/me` | Bearer | Current user info |
| GET | `/api/songs` | Viewer | List songs (optional `?search=`) with love_count, is_loved |
| GET | `/api/songs/{id}/stream` | Viewer | Stream audio file |
| POST / DELETE | `/api/songs/{id}/love` | Viewer | Love / unlove song |
| GET | `/api/songs/background/active` | Viewer | Active background image |
| GET | `/api/songs/background/random` | Viewer | Random background (for auto-change) |
| GET | `/api/songs/settings/auto-change-bg` | Viewer | Whether to auto-change background |
| GET | `/api/admin/songs` | Admin | List songs with love_count |
| POST | `/api/admin/songs` | Admin | Upload song |
| PATCH | `/api/admin/songs/{id}` | Admin | Update title/artist |
| DELETE | `/api/admin/songs/{id}` | Admin | Delete song |
| GET/POST/DELETE | `/api/admin/backgrounds` | Admin | List, upload, delete backgrounds |
| POST | `/api/admin/backgrounds/{id}/activate` | Admin | Set active background |
| GET | `/api/admin/users` | Admin | List users |
| DELETE | `/api/admin/users/{id}` | Admin | Remove user |
| GET/PATCH | `/api/admin/settings` | Admin | Get/update app settings (e.g. auto_change_background) |

---

## 7. Running the app

- **Local**: `.venv` → `pip install -r requirements.txt` → copy `.env.example` to `.env` (set `SECRET_KEY`) → `uvicorn app.main:app --reload` → open http://127.0.0.1:8000 and http://127.0.0.1:8000/admin.
- **Docker**: `docker compose up -d`; use volumes for `uploads` and DB so data persists.
- **VPS**: Push to GitHub; CI builds and pushes image; add secrets and (optionally) deploy job to pull and restart on the server.

---

## 8. Fixes and improvements made along the way

- **Auth**: Replaced passlib+bcrypt version clash with direct `bcrypt` for password hashing.
- **Streaming**: Player and admin do not use `<audio src="...">` for the stream URL; they `fetch` with `Authorization` and set `audio.src` to a blob URL so the request is authenticated.
- **Admin play**: Added a small player bar and per-song Play button on the admin page so admins can play songs without leaving `/admin`.
- **UX**: Single player bar (prev/play-pause/next/shuffle, now playing, love); song list with current track highlight and love count; admin sees love counts and can play from the list.

---

## 9. Possible next steps (not done yet)

- HTTPS and reverse proxy (e.g. Caddy/Nginx) on VPS.
- Optional viewer registration or invite flow.
- Optional “forgot password” or password change.
- Sort/filter by love count or date in admin.
- Volume control or progress bar in the player bar (optional).

---

*This file summarizes the NivPro project as of the last update. For day-to-day run instructions and layout, see [README.md](README.md).*
