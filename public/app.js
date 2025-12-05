const farmersList = document.getElementById('farmers');
const fieldsContainer = document.getElementById('fields');
const invoicesContainer = document.getElementById('invoices');
const auditContainer = document.getElementById('audit-log');
const userRoleSelect = document.getElementById('user-role');
const userIdInput = document.getElementById('user-id');

let permissions = {};
let selectedFarmer = null;
let selectedFields = [];
let currentInvoices = [];

function apiHeaders() {
  return {
    'Content-Type': 'application/json',
    'x-user-role': userRoleSelect.value,
    'x-user-id': userIdInput.value,
  };
}

async function fetchPermissions() {
  const res = await fetch('/api/permissions', { headers: apiHeaders() });
  const data = await res.json();
  permissions = data.permissions;
}

function can(action, resource) {
  return permissions?.[resource]?.[action]?.includes(userRoleSelect.value);
}

async function loadFarmers() {
  const res = await fetch('/api/farmers', { headers: apiHeaders() });
  const data = await res.json();
  farmersList.innerHTML = '';
  data.forEach((farmer) => {
    const li = document.createElement('li');
    li.textContent = farmer.name;
    li.classList.add('clickable');
    li.onclick = () => {
      selectedFarmer = farmer;
      renderFarmerSelection();
    };
    farmersList.appendChild(li);
  });
}

async function loadFields() {
  if (!selectedFarmer) return;
  const res = await fetch(`/api/farmers/${selectedFarmer.id}/fields`, { headers: apiHeaders() });
  selectedFields = await res.json();
  renderFields();
  loadAudit();
}

async function saveField(fieldId, updates) {
  await fetch(`/api/fields/${fieldId}`, {
    method: 'PATCH',
    headers: apiHeaders(),
    body: JSON.stringify(updates),
  });
  await loadFields();
}

async function loadInvoices() {
  if (!selectedFarmer) return;
  const res = await fetch(`/api/farmers/${selectedFarmer.id}/invoices`, { headers: apiHeaders() });
  currentInvoices = await res.json();
  renderInvoices();
}

async function createInvoice(payload) {
  await fetch(`/api/farmers/${selectedFarmer.id}/invoices`, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify(payload),
  });
  await loadInvoices();
  await loadAudit();
}

async function payInvoice(invoiceId) {
  await fetch(`/api/invoices/${invoiceId}/pay`, {
    method: 'PATCH',
    headers: apiHeaders(),
  });
  await loadInvoices();
  await loadAudit();
}

async function loadAudit() {
  if (!selectedFarmer) return;
  const params = new URLSearchParams({ farmerId: selectedFarmer.id });
  const res = await fetch(`/api/audit?${params.toString()}`, { headers: apiHeaders() });
  const entries = await res.json();
  renderAudit(entries);
}

async function loadEvents(fieldId) {
  const res = await fetch(`/api/fields/${fieldId}/events`, { headers: apiHeaders() });
  return res.json();
}

async function createEvent(fieldId, message) {
  await fetch(`/api/fields/${fieldId}/events`, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify({ message }),
  });
  await loadAudit();
  await loadFields();
}

function renderFarmerSelection() {
  document.querySelectorAll('#farmers li').forEach((li) => {
    li.classList.toggle('selected', li.textContent === selectedFarmer.name);
  });
  loadFields();
  loadInvoices();
}

function renderFields() {
  fieldsContainer.innerHTML = '';
  selectedFields.forEach(async (field) => {
    const card = document.createElement('div');
    card.className = 'field-card';
    const canUpdate = can('update', 'field');

    const header = document.createElement('div');
    header.innerHTML = `<strong>${field.name}</strong> <span class="badge">${field.crop}</span>`;

    const cropInput = document.createElement('input');
    cropInput.value = field.crop;
    cropInput.disabled = !canUpdate;

    const acresInput = document.createElement('input');
    acresInput.type = 'number';
    acresInput.value = field.acres;
    acresInput.disabled = !canUpdate;

    const soilInput = document.createElement('input');
    soilInput.value = field.soilType;
    soilInput.disabled = !canUpdate;

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save field';
    saveBtn.className = 'primary';
    saveBtn.disabled = !canUpdate;
    saveBtn.onclick = () => saveField(field.id, { crop: cropInput.value, acres: Number(acresInput.value), soilType: soilInput.value });

    card.append(header, labelWrap('Crop', cropInput), labelWrap('Acres', acresInput), labelWrap('Soil', soilInput), saveBtn);

    const eventsList = document.createElement('div');
    eventsList.className = 'events';
    const events = await loadEvents(field.id);
    eventsList.innerHTML = '<h4>Events</h4>' +
      events
        .map((evt) => `<div class="audit-entry"><strong>${new Date(evt.createdAt).toLocaleString()}</strong><div>${evt.message}</div></div>`)
        .join('');

    const eventInput = document.createElement('textarea');
    eventInput.placeholder = 'Add application or scouting note';
    eventInput.disabled = !can('create', 'event');

    const eventBtn = document.createElement('button');
    eventBtn.textContent = 'Log event';
    eventBtn.className = 'secondary';
    eventBtn.disabled = !can('create', 'event');
    eventBtn.onclick = () => {
      createEvent(field.id, eventInput.value);
      eventInput.value = '';
    };

    card.append(eventsList, eventInput, eventBtn);
    fieldsContainer.appendChild(card);
  });
}

function renderInvoices() {
  invoicesContainer.innerHTML = '';
  const canUpdateInvoice = can('update', 'invoice');

  currentInvoices.forEach((inv) => {
    const card = document.createElement('div');
    card.className = 'invoice-card';
    card.innerHTML = `
      <div><strong>Invoice ${inv.id}</strong></div>
      <div>Amount: $${inv.amount}</div>
      <div>Status: <span class="badge ${inv.status === 'paid' ? 'success' : 'warning'}">${inv.status}</span></div>
    `;
    const payBtn = document.createElement('button');
    payBtn.textContent = 'Mark paid';
    payBtn.className = 'primary';
    payBtn.disabled = !canUpdateInvoice || inv.status === 'paid';
    payBtn.onclick = () => payInvoice(inv.id);
    card.appendChild(payBtn);
    invoicesContainer.appendChild(card);
  });

  const invoiceForm = document.createElement('div');
  invoiceForm.className = 'invoice-card';
  invoiceForm.innerHTML = '<h4>Create invoice</h4>';
  const amountInput = document.createElement('input');
  amountInput.type = 'number';
  amountInput.placeholder = 'Amount in USD';
  const fieldSelect = document.createElement('select');
  selectedFields.forEach((f) => {
    const opt = document.createElement('option');
    opt.value = f.id;
    opt.textContent = f.name;
    fieldSelect.appendChild(opt);
  });
  const createBtn = document.createElement('button');
  createBtn.textContent = 'Create invoice';
  createBtn.className = 'primary';
  createBtn.disabled = !canUpdateInvoice;
  createBtn.onclick = () => createInvoice({ amount: Number(amountInput.value), fieldId: fieldSelect.value });
  invoiceForm.append(labelWrap('Field', fieldSelect), labelWrap('Amount', amountInput), createBtn);
  invoicesContainer.appendChild(invoiceForm);
}

function renderAudit(entries) {
  auditContainer.innerHTML = '';
  entries.forEach((entry) => {
    const div = document.createElement('div');
    div.className = 'audit-entry';
    div.innerHTML = `
      <div><strong>${entry.action}</strong> by ${entry.userId}</div>
      <div>${new Date(entry.timestamp).toLocaleString()}</div>
      <div class="muted">${JSON.stringify(entry.details || {})}</div>
    `;
    auditContainer.appendChild(div);
  });
}

function labelWrap(text, input) {
  const wrapper = document.createElement('label');
  wrapper.innerHTML = `<div>${text}</div>`;
  wrapper.appendChild(input);
  return wrapper;
}

userRoleSelect.onchange = async () => {
  await fetchPermissions();
  renderFields();
  renderInvoices();
  loadAudit();
};

userIdInput.onchange = () => {
  loadFields();
  loadInvoices();
  loadAudit();
};

(async function init() {
  await fetchPermissions();
  await loadFarmers();
})();
