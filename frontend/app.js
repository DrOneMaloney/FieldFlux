const API = "http://localhost:8000";

const invoiceList = document.getElementById("invoice-list");
const lineItemsContainer = document.getElementById("line-items");
const lineItemTemplate = document.getElementById("line-item-template");

function serializeLineItems() {
  return Array.from(lineItemsContainer.querySelectorAll(".line-item")).map((row, index) => ({
    description: row.querySelector("input[name='description']").value,
    quantity: parseFloat(row.querySelector("input[name='quantity']").value || 0),
    unit_price: parseFloat(row.querySelector("input[name='unit_price']").value || 0),
    tax_rate: parseFloat(row.querySelector("input[name='tax_rate']").value || 0) / 100,
    position: index,
  }));
}

function addLineItem() {
  const clone = lineItemTemplate.content.cloneNode(true);
  clone.querySelector(".remove").addEventListener("click", (e) => {
    e.target.closest(".line-item").remove();
  });
  lineItemsContainer.appendChild(clone);
}

document.getElementById("add-line").addEventListener("click", addLineItem);
addLineItem();

async function createFarmer(formData) {
  const payload = Object.fromEntries(formData.entries());
  const res = await fetch(`${API}/farmers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create farmer");
}

async function createField(formData) {
  const payload = Object.fromEntries(formData.entries());
  payload.acreage = payload.acreage ? parseFloat(payload.acreage) : null;
  payload.farmer_id = parseInt(payload.farmer_id, 10);
  const res = await fetch(`${API}/fields`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create field");
}

async function createInvoice(formData) {
  const payload = Object.fromEntries(formData.entries());
  payload.tax_rate = parseFloat(payload.tax_rate || 0) / 100;
  payload.discount_rate = parseFloat(payload.discount_rate || 0) / 100;
  payload.farmer_id = parseInt(payload.farmer_id, 10);
  payload.field_id = payload.field_id ? parseInt(payload.field_id, 10) : null;
  payload.line_items = serializeLineItems();
  payload.field_applications = payload.field_applications
    ? payload.field_applications.split(",").map((item) => item.trim()).filter(Boolean)
    : [];
  const res = await fetch(`${API}/invoices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create invoice");
  return res.json();
}

async function updateStatus(id, status) {
  const res = await fetch(`${API}/invoices/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Failed to update status");
}

async function recordPayment(id, amount) {
  const res = await fetch(`${API}/invoices/${id}/payments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount: parseFloat(amount) }),
  });
  if (!res.ok) throw new Error("Failed to record payment");
}

async function fetchInvoices() {
  const res = await fetch(`${API}/invoices`);
  const invoices = await res.json();
  renderInvoices(invoices);
}

function renderInvoices(invoices) {
  invoiceList.innerHTML = "";
  invoices.forEach((inv) => {
    const card = document.createElement("div");
    card.className = "invoice-card";
    card.innerHTML = `
      <div class="flex">
        <h3>Invoice #${inv.id}</h3>
        <span class="badge">${inv.status}</span>
      </div>
      <div class="meta">Farmer: ${inv.farmer.name}</div>
      <div class="meta">Field: ${inv.field ? inv.field.name : "N/A"}</div>
      <div class="balance">Balance: $${inv.outstanding_balance.toFixed(2)}</div>
      <small>Subtotal: $${inv.subtotal.toFixed(2)} | Tax: ${(inv.tax_rate * 100).toFixed(1)}% | Discount: ${(inv.discount_rate * 100).toFixed(1)}%</small>
      <div class="actions"></div>
      <div class="links">
        <a href="${API}/invoices/${inv.id}/html" target="_blank">HTML</a> ·
        <a href="${API}/invoices/${inv.id}/pdf" target="_blank">PDF</a>
      </div>
    `;
    const actions = card.querySelector(".actions");

    const sendBtn = document.createElement("button");
    sendBtn.textContent = "Send";
    sendBtn.addEventListener("click", async () => {
      await updateStatus(inv.id, "sent");
      fetchInvoices();
    });

    const payBtn = document.createElement("button");
    payBtn.textContent = "Record Payment";
    payBtn.addEventListener("click", async () => {
      const amount = prompt("Payment amount");
      if (amount) {
        await recordPayment(inv.id, amount);
        fetchInvoices();
      }
    });

    actions.appendChild(sendBtn);
    actions.appendChild(payBtn);
    invoiceList.appendChild(card);
  });
}

const farmerForm = document.getElementById("farmer-form");
farmerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  await createFarmer(new FormData(farmerForm));
  farmerForm.reset();
});

const fieldForm = document.getElementById("field-form");
fieldForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  await createField(new FormData(fieldForm));
  fieldForm.reset();
});

const invoiceForm = document.getElementById("invoice-form");
invoiceForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  await createInvoice(new FormData(invoiceForm));
  invoiceForm.reset();
  lineItemsContainer.innerHTML = "";
  addLineItem();
  fetchInvoices();
});

fetchInvoices();
const API_BASE = (() => {
  if (typeof window !== "undefined") {
    const { hostname, protocol } = window.location;
    if (hostname.endsWith("app.github.dev")) {
      // Map the current preview host to the forwarded backend port in Codespaces
      const apiHost = hostname.replace(/-\d+\.app\.github\.dev$/, "-8000.app.github.dev");
      return `${protocol}//${apiHost}`;
    }
  }
  return "http://localhost:8000";
})();

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
