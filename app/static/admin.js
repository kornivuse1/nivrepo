(function () {
  const API = "/api";
  const TOKEN_KEY = "nivpro_admin_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }
  function setToken(t) {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  }
  function authHeaders() {
    const t = getToken();
    return t ? { Authorization: "Bearer " + t } : {};
  }

  const loginSection = document.getElementById("login-section");
  const adminSection = document.getElementById("admin-section");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const userArea = document.getElementById("user-area");
  const uploadForm = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const uploadStatus = document.getElementById("upload-status");
  const bgUploadForm = document.getElementById("bg-upload-form");
  const bgFileInput = document.getElementById("bg-file-input");
  const bgUploadStatus = document.getElementById("bg-upload-status");
  const searchEl = document.getElementById("search");
  const songList = document.getElementById("song-list");
  const bgList = document.getElementById("bg-list");
  const usersList = document.getElementById("users-list");
  const autoChangeBgToggle = document.getElementById("auto-change-bg-toggle");
  const adminAudio = document.getElementById("admin-audio");
  const adminPlayPauseBtn = document.getElementById("admin-play-pause-btn");
  const adminNowPlaying = document.getElementById("admin-now-playing");

  async function checkAuth() {
    const token = getToken();
    if (!token) return false;
    const r = await fetch(API + "/auth/me", { headers: authHeaders() });
    if (!r.ok) { setToken(null); return false; }
    const user = await r.json();
    if (user.role !== "admin") { setToken(null); return false; }
    return user;
  }

  function showLogin() {
    loginSection.classList.remove("hidden");
    adminSection.classList.add("hidden");
    userArea.textContent = "";
  }
  function showAdmin(user) {
    loginSection.classList.add("hidden");
    adminSection.classList.remove("hidden");
    userArea.innerHTML = "<span>" + user.username + "</span> <button type=\"button\" id=\"logout-btn\">Log out</button>";
    document.getElementById("logout-btn").onclick = function () { setToken(null); showLogin(); };
    loadSongs();
    loadBackgrounds();
    loadUsers();
    loadSettings();
  }

  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    loginError.textContent = "";
    const formData = new FormData(loginForm);
    const body = new URLSearchParams({ username: formData.get("username"), password: formData.get("password") });
    const r = await fetch(API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    if (!r.ok) {
      loginError.textContent = "Invalid username or password.";
      return;
    }
    const data = await r.json();
    setToken(data.access_token);
    const user = await checkAuth();
    if (user) showAdmin(user);
    else loginError.textContent = "Admin access required.";
  });

  async function loadSongs(query) {
    const url = query ? API + "/admin/songs?search=" + encodeURIComponent(query) : API + "/admin/songs";
    const r = await fetch(url, { headers: authHeaders() });
    if (!r.ok) { showLogin(); return; }
    const songs = await r.json();
    songList.innerHTML = songs.map(function (s) {
      return "<li data-id=\"" + s.id + "\"><div class=\"song-info\"><input type=\"text\" class=\"song-title\" value=\"" + escapeHtml(s.title) + "\" data-field=\"title\"><span> – </span><input type=\"text\" class=\"song-artist\" value=\"" + escapeHtml(s.artist) + "\" data-field=\"artist\"></div><div class=\"song-actions\"><span class=\"love-count-admin\">❤ " + (s.love_count || 0) + "</span><button type=\"button\" class=\"play-btn-admin\" title=\"Play\">▶</button><button type=\"button\" class=\"save-btn\">Save</button><button type=\"button\" class=\"delete\">Delete</button></div></li>";
    }).join("");
    songList.querySelectorAll(".play-btn-admin").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const li = btn.closest("li");
        const id = parseInt(li.dataset.id);
        const title = li.querySelector(".song-title").value.trim();
        const artist = li.querySelector(".song-artist").value.trim();
        playSongInAdmin(id, title, artist);
      });
    });
    songList.querySelectorAll(".save-btn").forEach(function (btn) {
      btn.addEventListener("click", async function (e) {
        e.stopPropagation();
        const li = btn.closest("li");
        const id = parseInt(li.dataset.id);
        const title = li.querySelector(".song-title").value.trim();
        const artist = li.querySelector(".song-artist").value.trim();
        const r = await fetch(API + "/admin/songs/" + id, {
          method: "PATCH",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ title: title, artist: artist }),
        });
        if (r.ok) {
          btn.textContent = "Saved!";
          setTimeout(function () { btn.textContent = "Save"; }, 2000);
          loadSongs(searchEl.value.trim());
        }
      });
    });
    songList.querySelectorAll(".delete").forEach(function (btn) {
      btn.addEventListener("click", async function (e) {
        e.stopPropagation();
        const id = btn.closest("li").dataset.id;
        if (!confirm("Delete this song?")) return;
        const r = await fetch(API + "/admin/songs/" + id, { method: "DELETE", headers: authHeaders() });
        if (r.ok) loadSongs(searchEl.value.trim());
      });
    });
  }

  async function playSongInAdmin(songId, title, artist) {
    adminNowPlaying.textContent = (title || "Unknown") + " – " + (artist || "");
    if (adminAudio.src && adminAudio.src.startsWith("blob:")) {
      URL.revokeObjectURL(adminAudio.src);
    }
    try {
      const r = await fetch(API + "/songs/" + songId + "/stream", { headers: authHeaders() });
      if (!r.ok) {
        adminNowPlaying.textContent = "Could not load song.";
        return;
      }
      const blob = await r.blob();
      adminAudio.src = URL.createObjectURL(blob);
      adminAudio.play();
      adminPlayPauseBtn.textContent = "⏸";
      adminPlayPauseBtn.classList.add("pause-btn");
    } catch (err) {
      adminNowPlaying.textContent = "Error loading song.";
    }
  }

  if (adminPlayPauseBtn) {
    adminPlayPauseBtn.addEventListener("click", function () {
      if (adminAudio.paused) {
        adminAudio.play();
        adminPlayPauseBtn.textContent = "⏸";
        adminPlayPauseBtn.classList.add("pause-btn");
      } else {
        adminAudio.pause();
        adminPlayPauseBtn.textContent = "▶";
        adminPlayPauseBtn.classList.remove("pause-btn");
      }
    });
  }
  if (adminAudio) {
    adminAudio.addEventListener("ended", function () {
      adminPlayPauseBtn.textContent = "▶";
      adminPlayPauseBtn.classList.remove("pause-btn");
    });
  }

  async function loadBackgrounds() {
    const r = await fetch(API + "/admin/backgrounds", { headers: authHeaders() });
    if (!r.ok) return;
    const images = await r.json();
    bgList.innerHTML = images.map(function (img) {
      return "<li data-id=\"" + img.id + "\"><span>" + escapeHtml(img.filename) + (img.is_active ? " <strong>(active)</strong>" : "") + "</span><div><button type=\"button\" class=\"activate-btn\"" + (img.is_active ? " disabled" : "") + ">Activate</button><button type=\"button\" class=\"delete\">Delete</button></div></li>";
    }).join("");
    bgList.querySelectorAll(".activate-btn").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        const id = btn.closest("li").dataset.id;
        const r = await fetch(API + "/admin/backgrounds/" + id + "/activate", {
          method: "POST",
          headers: authHeaders(),
        });
        if (r.ok) loadBackgrounds();
      });
    });
    bgList.querySelectorAll(".delete").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        const id = btn.closest("li").dataset.id;
        if (!confirm("Delete this background image?")) return;
        const r = await fetch(API + "/admin/backgrounds/" + id, { method: "DELETE", headers: authHeaders() });
        if (r.ok) loadBackgrounds();
      });
    });
  }

  async function loadUsers() {
    const r = await fetch(API + "/admin/users", { headers: authHeaders() });
    if (!r.ok) return;
    const users = await r.json();
    usersList.innerHTML = users.map(function (u) {
      return "<li data-id=\"" + u.id + "\"><span><strong>" + escapeHtml(u.username) + "</strong> (" + escapeHtml(u.role) + ")</span><button type=\"button\" class=\"delete\">Remove</button></li>";
    }).join("");
    usersList.querySelectorAll(".delete").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        const id = btn.closest("li").dataset.id;
        if (!confirm("Remove this user? They will lose access.")) return;
        const r = await fetch(API + "/admin/users/" + id, { method: "DELETE", headers: authHeaders() });
        if (r.ok) loadUsers();
      });
    });
  }

  async function loadSettings() {
    const r = await fetch(API + "/admin/settings", { headers: authHeaders() });
    if (!r.ok) return;
    const settings = await r.json();
    autoChangeBgToggle.checked = settings.auto_change_background || false;
  }

  autoChangeBgToggle.addEventListener("change", async function () {
    const r = await fetch(API + "/admin/settings", {
      method: "PATCH",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ auto_change_background: autoChangeBgToggle.checked }),
    });
    if (!r.ok) {
      autoChangeBgToggle.checked = !autoChangeBgToggle.checked;
    }
  });

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  uploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    uploadStatus.textContent = "Uploading...";
    const file = fileInput.files[0];
    if (!file) { uploadStatus.textContent = "Choose a file."; return; }
    const formData = new FormData();
    formData.append("file", file);
    const r = await fetch(API + "/admin/songs", {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    if (!r.ok) {
      uploadStatus.textContent = "Upload failed: " + (await r.json().catch(function () { return {}; })).detail || r.status;
      return;
    }
    uploadStatus.textContent = "Uploaded.";
    fileInput.value = "";
    loadSongs(searchEl.value.trim());
  });

  bgUploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    bgUploadStatus.textContent = "Uploading...";
    const file = bgFileInput.files[0];
    if (!file) { bgUploadStatus.textContent = "Choose a file."; return; }
    const formData = new FormData();
    formData.append("file", file);
    const r = await fetch(API + "/admin/backgrounds", {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    if (!r.ok) {
      bgUploadStatus.textContent = "Upload failed: " + (await r.json().catch(function () { return {}; })).detail || r.status;
      return;
    }
    bgUploadStatus.textContent = "Uploaded.";
    bgFileInput.value = "";
    loadBackgrounds();
  });

  let searchTimeout;
  searchEl.addEventListener("input", function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () { loadSongs(searchEl.value.trim()); }, 200);
  });

  (async function () {
    const user = await checkAuth();
    if (user) showAdmin(user);
    else showLogin();
  })();
})();
