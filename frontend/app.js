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
