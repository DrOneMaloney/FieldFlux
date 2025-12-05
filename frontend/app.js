const API_BASE = "http://localhost:8000";

const store = (() => {
  let state = {
    accessToken: null,
    refreshToken: null,
    user: null,
  };
  const listeners = new Set();

  const notify = () => listeners.forEach((cb) => cb({ ...state }));

  return {
    subscribe(cb) {
      listeners.add(cb);
      cb({ ...state });
      return () => listeners.delete(cb);
    },
    setAuth(accessToken, refreshToken) {
      state = { ...state, accessToken, refreshToken };
      notify();
    },
    setUser(user) {
      state = { ...state, user };
      notify();
    },
    clear() {
      state = { accessToken: null, refreshToken: null, user: null };
      notify();
    },
    getState() {
      return { ...state };
    },
  };
})();

async function api(path, options = {}) {
  const { accessToken } = store.getState();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(detail.detail || detail.message || "Request failed");
  }
  return response.json();
}

async function handleSignup(event) {
  event.preventDefault();
  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;
  const statusEl = document.getElementById("signup-status");
  statusEl.textContent = "Signing up...";
  try {
    await api("/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    statusEl.textContent = "Signup successful! Check your email for verification.";
  } catch (err) {
    statusEl.textContent = err.message;
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const statusEl = document.getElementById("login-status");
  statusEl.textContent = "Logging in...";
  try {
    const tokens = await api("/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    store.setAuth(tokens.access_token, tokens.refresh_token);
    await fetchProfile();
    statusEl.textContent = "Logged in";
  } catch (err) {
    statusEl.textContent = err.message;
  }
}

async function handleLogout() {
  const statusEl = document.getElementById("login-status");
  statusEl.textContent = "Logging out...";
  try {
    await api("/logout", { method: "POST" });
  } catch (err) {
    console.error(err);
  }
  store.clear();
  document.getElementById("profile").textContent = "";
  statusEl.textContent = "Logged out";
}

async function handleResetRequest(event) {
  event.preventDefault();
  const email = document.getElementById("reset-email").value;
  const statusEl = document.getElementById("reset-status");
  statusEl.textContent = "Requesting reset...";
  try {
    const result = await api("/password-reset/request", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    statusEl.textContent = result.message;
  } catch (err) {
    statusEl.textContent = err.message;
  }
}

async function handleResetConfirm(event) {
  event.preventDefault();
  const token = document.getElementById("reset-token").value;
  const newPassword = document.getElementById("reset-new-password").value;
  const statusEl = document.getElementById("reset-status");
  statusEl.textContent = "Resetting password...";
  try {
    const result = await api("/password-reset/confirm", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    statusEl.textContent = result.message;
  } catch (err) {
    statusEl.textContent = err.message;
  }
}

async function fetchProfile() {
  try {
    const me = await api("/me");
    store.setUser(me);
  } catch (err) {
    console.error("Failed to load profile", err);
  }
}

function renderProfile(state) {
  const profile = document.getElementById("profile");
  if (!state.user) {
    profile.textContent = "No active session";
    return;
  }
  profile.textContent = `Logged in as ${state.user.email} (verified: ${state.user.is_verified})`;
}

function renderTokens(state) {
  const tokens = document.getElementById("tokens");
  tokens.textContent = state.accessToken
    ? `Access: ${state.accessToken.slice(0, 20)}... Refresh: ${state.refreshToken?.slice(0, 20)}...`
    : "No tokens";
}

function init() {
  document.getElementById("signup-form").addEventListener("submit", handleSignup);
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("logout").addEventListener("click", handleLogout);
  document.getElementById("reset-request-form").addEventListener("submit", handleResetRequest);
  document.getElementById("reset-confirm-form").addEventListener("submit", handleResetConfirm);
  store.subscribe((state) => {
    renderProfile(state);
    renderTokens(state);
  });
}

window.addEventListener("DOMContentLoaded", init);
