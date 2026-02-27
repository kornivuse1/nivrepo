(function () {
  const API = "/api";
  const TOKEN_KEY = "nivpro_token";

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
  const playerSection = document.getElementById("player-section");
  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");
  const loginError = document.getElementById("login-error");
  const signupError = document.getElementById("signup-error");
  const userArea = document.getElementById("user-area");
  const searchEl = document.getElementById("search");
  const songList = document.getElementById("song-list");
  const audio = document.getElementById("audio");
  const nowPlayingTitle = document.getElementById("now-playing-title");
  const nowPlayingArtist = document.getElementById("now-playing-artist");
  const playPauseBtn = document.getElementById("play-pause-btn");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");
  const shuffleBtn = document.getElementById("shuffle-btn");
  const loveBtn = document.getElementById("love-btn");
  const timeCurrentEl = document.getElementById("time-current");
  const progressBar = document.getElementById("progress-bar");
  const timeTotalEl = document.getElementById("time-total");
  const timeLeftEl = document.getElementById("time-left");

  function formatTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  let progressSeeking = false;

  function updateProgressDisplay() {
    if (progressSeeking) return;
    const t = audio.currentTime;
    const d = audio.duration;
    if (Number.isFinite(d)) {
      progressBar.max = Math.floor(d);
      progressBar.value = Math.floor(t);
      timeTotalEl.textContent = formatTime(d);
      const left = Math.max(0, d - t);
      timeLeftEl.textContent = "−" + formatTime(left);
    }
    timeCurrentEl.textContent = formatTime(t);
  }

  let currentPlaylist = [];
  let currentIndex = -1;
  let currentSong = null;
  let isShuffled = false;
  let isPlaying = false;
  let autoChangeBg = false;

  async function checkAuth() {
    const token = getToken();
    if (!token) return false;
    const r = await fetch(API + "/auth/me", { headers: authHeaders() });
    if (!r.ok) { setToken(null); return false; }
    return await r.json();
  }

  async function updateSignupVisibility() {
    try {
      const r = await fetch(API + "/auth/registration-allowed");
      const data = await r.json().catch(function () { return { allow_registration: false }; });
      const allow = data.allow_registration === true;
      const signupToggle = document.getElementById("show-signup");
      if (signupToggle && signupToggle.closest("p")) {
        signupToggle.closest("p").style.display = allow ? "" : "none";
      }
    } catch (e) {
      const p = document.getElementById("show-signup") && document.getElementById("show-signup").closest("p");
      if (p) p.style.display = "none";
    }
  }

  function showLogin() {
    loginSection.classList.remove("hidden");
    playerSection.classList.add("hidden");
    userArea.textContent = "";
    loginForm.classList.remove("hidden");
    signupForm.classList.add("hidden");
    loginError.textContent = "";
    signupError.textContent = "";
    updateSignupVisibility();
  }

  async function loadBackground(url) {
    try {
      if (url && url.startsWith("blob:")) {
        URL.revokeObjectURL(url);
      }
      const r = await fetch(API + "/songs/background/active", { headers: authHeaders() });
      if (r.ok) {
        const blob = await r.blob();
        const newUrl = URL.createObjectURL(blob);
        document.body.style.backgroundImage = "url(" + newUrl + ")";
        document.body.classList.add("has-background");
        return newUrl;
      }
    } catch (e) {
      // No background or error - ignore
    }
    return null;
  }

  async function loadRandomBackground() {
    try {
      const r = await fetch(API + "/songs/background/random", { headers: authHeaders() });
      if (r.ok) {
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const oldUrl = document.body.style.backgroundImage.match(/url\(([^)]+)\)/);
        if (oldUrl && oldUrl[1] && oldUrl[1].startsWith("blob:")) {
          URL.revokeObjectURL(oldUrl[1]);
        }
        document.body.style.backgroundImage = "url(" + url + ")";
        document.body.classList.add("has-background");
        return url;
      }
    } catch (e) {
      // No background or error - ignore
    }
    return null;
  }

  async function checkAutoChangeSetting() {
    try {
      const r = await fetch(API + "/songs/settings/auto-change-bg", { headers: authHeaders() });
      if (r.ok) {
        const data = await r.json();
        autoChangeBg = data.auto_change_background || false;
      }
    } catch (e) {
      autoChangeBg = false;
    }
  }

  function shuffleArray(arr) {
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  function updatePlayPauseButton() {
    if (isPlaying) {
      playPauseBtn.textContent = "⏸";
      playPauseBtn.classList.add("pause-btn");
      playPauseBtn.classList.remove("play-btn");
    } else {
      playPauseBtn.textContent = "▶";
      playPauseBtn.classList.add("play-btn");
      playPauseBtn.classList.remove("pause-btn");
    }
  }

  function updateLoveButton(loved) {
    if (loved) {
      loveBtn.textContent = "❤";
      loveBtn.classList.add("loved");
    } else {
      loveBtn.textContent = "♡";
      loveBtn.classList.remove("loved");
    }
  }

  async function playSong(song, index) {
    currentIndex = index;
    currentSong = song;
    nowPlayingTitle.textContent = song.title;
    nowPlayingArtist.textContent = song.artist;
    updateLoveButton(song.is_loved);
    progressBar.value = 0;
    progressBar.max = 0;
    timeCurrentEl.textContent = "0:00";
    timeTotalEl.textContent = "0:00";
    timeLeftEl.textContent = "";
    if (audio.src && audio.src.startsWith("blob:")) URL.revokeObjectURL(audio.src);
    const r = await fetch(API + "/songs/" + song.id + "/stream", { headers: authHeaders() });
    if (!r.ok) {
      nowPlayingTitle.textContent = "Could not load song.";
      nowPlayingArtist.textContent = "";
      playNext();
      return;
    }
    const blob = await r.blob();
    audio.src = URL.createObjectURL(blob);
    audio.play();
    isPlaying = true;
    updatePlayPauseButton();
    if (autoChangeBg) {
      await loadRandomBackground();
    }
  }

  function playNext() {
    if (currentPlaylist.length === 0) return;
    if (isShuffled && currentIndex === -1) {
      currentPlaylist = shuffleArray(currentPlaylist);
      currentIndex = 0;
    } else if (isShuffled) {
      currentIndex = (currentIndex + 1) % currentPlaylist.length;
    } else {
      currentIndex = (currentIndex + 1) % currentPlaylist.length;
    }
    playSong(currentPlaylist[currentIndex], currentIndex);
  }

  function playPrev() {
    if (currentPlaylist.length === 0) return;
    if (isShuffled) {
      currentIndex = (currentIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
    } else {
      currentIndex = (currentIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
    }
    playSong(currentPlaylist[currentIndex], currentIndex);
  }

  function showPlayer(user) {
    loginSection.classList.add("hidden");
    playerSection.classList.remove("hidden");
    userArea.innerHTML = "<span>" + user.username + "</span> <button type=\"button\" id=\"logout-btn\">Log out</button>";
    document.getElementById("logout-btn").onclick = function () { setToken(null); showLogin(); };
    loadSongs();
    loadBackground();
    checkAutoChangeSetting();
  }

  document.getElementById("show-signup").addEventListener("click", function (e) {
    e.preventDefault();
    loginForm.classList.add("hidden");
    signupForm.classList.remove("hidden");
    loginError.textContent = "";
    signupError.textContent = "";
  });
  document.getElementById("show-login").addEventListener("click", function (e) {
    e.preventDefault();
    signupForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
    loginError.textContent = "";
    signupError.textContent = "";
  });

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
    if (user) showPlayer(user);
  });

  signupForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    signupError.textContent = "";
    const formData = new FormData(signupForm);
    const password = formData.get("password");
    const password_confirm = formData.get("password_confirm");
    if (password !== password_confirm) {
      signupError.textContent = "Passwords do not match.";
      return;
    }
    if (String(password).length < 6) {
      signupError.textContent = "Password must be at least 6 characters.";
      return;
    }
    const r = await fetch(API + "/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: formData.get("username"),
        password: password,
        password_confirm: password_confirm,
      }),
    });
    if (!r.ok) {
      const err = await r.json().catch(function () { return {}; });
      const detail = Array.isArray(err.detail) ? err.detail.map(function (d) { return d.msg || d; }).join(" ") : err.detail;
      signupError.textContent = detail || "Sign up failed.";
      return;
    }
    const data = await r.json();
    setToken(data.access_token);
    const user = await checkAuth();
    if (user) showPlayer(user);
  });

  playPauseBtn.addEventListener("click", function () {
    if (!currentSong) {
      if (currentPlaylist.length > 0) {
        currentIndex = isShuffled ? -1 : 0;
        if (isShuffled) {
          currentPlaylist = shuffleArray(currentPlaylist);
          currentIndex = 0;
        }
        playSong(currentPlaylist[currentIndex], currentIndex);
      }
      return;
    }
    if (isPlaying) {
      audio.pause();
      isPlaying = false;
    } else {
      audio.play();
      isPlaying = true;
    }
    updatePlayPauseButton();
  });

  prevBtn.addEventListener("click", function () {
    if (currentPlaylist.length === 0) return;
    if (currentIndex === -1) {
      currentIndex = currentPlaylist.length - 1;
    }
    playPrev();
  });

  nextBtn.addEventListener("click", function () {
    if (currentPlaylist.length === 0) return;
    if (currentIndex === -1) {
      currentIndex = 0;
    }
    playNext();
  });

  shuffleBtn.addEventListener("click", function () {
    isShuffled = !isShuffled;
    if (isShuffled) {
      shuffleBtn.classList.add("active");
      if (currentPlaylist.length > 0 && currentIndex >= 0) {
        const currentSong = currentPlaylist[currentIndex];
        currentPlaylist = shuffleArray(currentPlaylist);
        currentIndex = currentPlaylist.findIndex(function (s) { return s.id === currentSong.id; });
        if (currentIndex === -1) currentIndex = 0;
      }
    } else {
      shuffleBtn.classList.remove("active");
    }
  });

  loveBtn.addEventListener("click", async function () {
    if (!currentSong) return;
    const isLoved = currentSong.is_loved;
    const method = isLoved ? "DELETE" : "POST";
    const r = await fetch(API + "/songs/" + currentSong.id + "/love", {
      method: method,
      headers: authHeaders(),
    });
    if (r.ok) {
      currentSong.is_loved = !isLoved;
      updateLoveButton(currentSong.is_loved);
      // Update in playlist
      const songInList = currentPlaylist.find(function (s) { return s.id === currentSong.id; });
      if (songInList) {
        songInList.is_loved = currentSong.is_loved;
        songInList.love_count += isLoved ? -1 : 1;
        loadSongs(searchEl.value.trim());
      }
    }
  });

  audio.addEventListener("ended", function () {
    isPlaying = false;
    updatePlayPauseButton();
    if (currentPlaylist.length > 0 && currentIndex >= 0) {
      playNext();
    }
  });

  audio.addEventListener("play", function () {
    isPlaying = true;
    updatePlayPauseButton();
  });

  audio.addEventListener("pause", function () {
    isPlaying = false;
    updatePlayPauseButton();
  });

  audio.addEventListener("timeupdate", updateProgressDisplay);
  audio.addEventListener("loadedmetadata", function () {
    progressBar.max = Math.floor(audio.duration) || 0;
    timeTotalEl.textContent = formatTime(audio.duration);
    updateProgressDisplay();
  });

  progressBar.addEventListener("input", function () {
    progressSeeking = true;
    const val = parseInt(progressBar.value, 10);
    if (Number.isFinite(val)) audio.currentTime = val;
    timeCurrentEl.textContent = formatTime(val);
    if (Number.isFinite(audio.duration)) {
      timeLeftEl.textContent = "−" + formatTime(Math.max(0, audio.duration - val));
    }
  });
  progressBar.addEventListener("change", function () {
    progressSeeking = false;
    if (Number.isFinite(audio.duration)) audio.currentTime = parseInt(progressBar.value, 10);
    updateProgressDisplay();
  });

  async function loadSongs(query) {
    const url = query ? API + "/songs?search=" + encodeURIComponent(query) : API + "/songs";
    const r = await fetch(url, { headers: authHeaders() });
    if (!r.ok) { showLogin(); return; }
    const songs = await r.json();
    currentPlaylist = songs;
    if (isShuffled && currentIndex >= 0 && currentSong) {
      const currentSongId = currentSong.id;
      currentPlaylist = shuffleArray(currentPlaylist);
      currentIndex = currentPlaylist.findIndex(function (s) { return s.id === currentSongId; });
      if (currentIndex === -1) currentIndex = -1;
    }
    songList.innerHTML = songs.map(function (s) {
      const dur = s.duration_seconds != null ? Math.floor(s.duration_seconds / 60) + ":" + String(Math.floor(s.duration_seconds % 60)).padStart(2, "0") : "";
      const heartClass = s.is_loved ? "loved" : "";
      return "<li data-id=\"" + s.id + "\" class=\"" + (s.id === (currentSong ? currentSong.id : -1) ? "current" : "") + "\"><span><strong>" + escapeHtml(s.title) + "</strong> – " + escapeHtml(s.artist) + (dur ? " <small>(" + dur + ")</small>" : "") + "</span><span class=\"song-love\"><span class=\"love-count\">" + s.love_count + "</span> <span class=\"love-icon " + heartClass + "\">" + (s.is_loved ? "❤" : "♡") + "</span></span></li>";
    }).join("");
    songList.querySelectorAll("li").forEach(function (li) {
      li.addEventListener("click", async function () {
        const id = parseInt(li.dataset.id);
        const song = currentPlaylist.find(function (s) { return s.id === id; });
        if (!song) return;
        let index = currentPlaylist.indexOf(song);
        if (isShuffled && currentIndex === -1) {
          currentPlaylist = shuffleArray(currentPlaylist);
          index = currentPlaylist.indexOf(song);
        }
        await playSong(song, index);
      });
    });
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  let searchTimeout;
  searchEl.addEventListener("input", function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () { loadSongs(searchEl.value.trim()); }, 200);
  });

  (async function () {
    const user = await checkAuth();
    if (user) showPlayer(user);
    else {
      showLogin();
    }
  })();
})();
