# Push NivPro to GitHub

Do this on your laptop (in PowerShell or Command Prompt) from the project folder. Git must be installed.

---

## Step 1: Create the repository on GitHub (in the browser)

1. Go to **https://github.com/new**
2. **Repository name**: `nivpro` (or any name you like)
3. **Description**: optional, e.g. "Music player server"
4. Choose **Private** or **Public**
5. **Do not** check "Add a README", "Add .gitignore", or "Choose a license" (we already have these)
6. Click **Create repository**

7. Copy the repo URL GitHub shows. It will look like:
   - HTTPS: `https://github.com/YOUR_USERNAME/nivpro.git`
   - or SSH: `git@github.com:YOUR_USERNAME/nivpro.git`

Replace `YOUR_USERNAME` with your actual GitHub username in the commands below.

---

## Step 2: Open a terminal in the project folder

```powershell
cd c:\Users\korni\NivPro
```

---

## Step 3: Initialize Git (if not already done) and make the first commit

Run these one by one:

```powershell
git init
git branch -M main
git add .
git status
```

Check that `git status` does **not** list `.env` or `.venv` (they should be ignored). If they appear, stop and fix `.gitignore` first.

Then:

```powershell
git commit -m "Initial commit: NivPro music player server"
```

---

## Step 4: Add GitHub as remote and push

Replace `YOUR_USERNAME` with your GitHub username (and `nivpro` if you used a different repo name):

```powershell
git remote add origin https://github.com/YOUR_USERNAME/nivpro.git
git push -u origin main
```

If GitHub asks for login, use your GitHub username and a **Personal Access Token** (not your password). To create one: GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic), enable `repo`, then paste the token when prompted for password.

---

## Step 5: Make the package public (for Docker image)

After the first push, GitHub will build a "package" for the Docker image. To let the VPS pull it without auth:

1. Open your repo on GitHub.
2. On the right, under **About**, click **Packages**, or go to:  
   `https://github.com/YOUR_USERNAME/nivpro/pkgs/container/nivpro`
3. Open the package → **Package settings** → **Change visibility** → **Public**.

(You can do this later when you set up the VPS.)

---

Done. Your project is on GitHub. When you have the VPS, we’ll add the secrets and deploy.
