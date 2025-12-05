let selectedFarmerId = null;
let farmersCache = [];
const farmerSelect = document.getElementById('farmer-select');
const farmerStatus = document.getElementById('farmer-status');
const fieldStatus = document.getElementById('field-status');
const fieldList = document.getElementById('field-list');
const summaryBody = document.getElementById('summary-body');
const totalAcresLabel = document.getElementById('total-acres');
const fieldNameInput = document.getElementById('field-name');
const fieldNotesInput = document.getElementById('field-notes');

const map = L.map('map').setView([39, -96], 4);
const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
const satellite = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
  maxZoom: 19,
  attribution: '&copy; Google'
});
L.control.layers({ 'Streets': streets, 'Satellite': satellite }).addTo(map);

const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);
const drawControl = new L.Control.Draw({
  edit: {
    featureGroup: drawnItems,
    poly: { allowIntersection: false }
  },
  draw: {
    circle: false,
    marker: false,
    polyline: false,
    rectangle: false,
    circlemarker: false,
    polygon: {
      allowIntersection: false,
      showArea: true,
      shapeOptions: { color: '#1d4ed8' }
    }
  }
});
map.addControl(drawControl);

function setStatus(el, message, success = false) {
  el.textContent = message || '';
  el.style.color = success ? '#16a34a' : '#dc2626';
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

async function loadFarmers(preserveSelection = true) {
  try {
    const farmers = await fetchJson('/api/farmers');
    farmersCache = farmers;
    farmerSelect.innerHTML = '';
    farmers.forEach(farmer => {
      const opt = document.createElement('option');
      opt.value = farmer.id;
      opt.textContent = `${farmer.name} (${farmer.fieldCount} fields)`;
      farmerSelect.appendChild(opt);
    });
    if (!farmers.length) {
      const opt = document.createElement('option');
      opt.textContent = 'Add a farmer to get started';
      opt.disabled = true;
      farmerSelect.appendChild(opt);
      selectedFarmerId = null;
      totalAcresLabel.textContent = '0';
      renderSummaryTable([]);
      drawnItems.clearLayers();
      renderFieldList([]);
      return;
    }
    if (preserveSelection && selectedFarmerId) {
      farmerSelect.value = selectedFarmerId;
    } else {
      selectedFarmerId = farmers[0].id;
      farmerSelect.value = selectedFarmerId;
    }
    renderSummaryTable(farmers);
    updateTotalAcres();
    await loadFieldsForFarmer(selectedFarmerId);
  } catch (err) {
    setStatus(farmerStatus, err.message);
  }
}

function renderSummaryTable(farmers) {
  summaryBody.innerHTML = '';
  farmers.forEach(farmer => {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${farmer.name}</td><td><span class="badge">${farmer.fieldCount}</span></td><td>${farmer.totalAcres || 0}</td>`;
    summaryBody.appendChild(row);
  });
}

function updateTotalAcres() {
  const farmer = farmersCache.find(f => f.id === selectedFarmerId);
  totalAcresLabel.textContent = farmer ? farmer.totalAcres : 0;
}

async function loadFieldsForFarmer(farmerId) {
  if (!farmerId) return;
  try {
    const fields = await fetchJson(`/api/farmers/${farmerId}/fields`);
    drawnItems.clearLayers();
    fields.forEach(field => addFieldLayer(field));
    renderFieldList(fields);
    updateTotalAcres();
  } catch (err) {
    setStatus(fieldStatus, err.message);
  }
}

function addFieldLayer(field) {
  const layer = L.geoJSON(field.geometry, {
    style: { color: '#1d4ed8', weight: 2, fillOpacity: 0.2 }
  });
  layer.eachLayer(l => {
    l.fieldId = field.id;
    l.bindPopup(`<strong>${field.name}</strong><br/>${field.acres} acres`);
    drawnItems.addLayer(l);
  });
}

function renderFieldList(fields) {
  fieldList.innerHTML = '';
  fields.forEach(field => {
    const item = document.createElement('li');
    item.innerHTML = `<span>${field.name}</span><span>${field.acres} acres</span>`;
    fieldList.appendChild(item);
  });
}

async function handleCreateFarmer() {
  const name = document.getElementById('new-farmer-name').value.trim();
  if (!name) return setStatus(farmerStatus, 'Enter a farmer name.');
  try {
    await fetchJson('/api/farmers', { method: 'POST', body: JSON.stringify({ name }) });
    document.getElementById('new-farmer-name').value = '';
    setStatus(farmerStatus, 'Farmer created', true);
    await loadFarmers(false);
  } catch (err) {
    setStatus(farmerStatus, err.message);
  }
}

document.getElementById('add-farmer').addEventListener('click', handleCreateFarmer);
farmerSelect.addEventListener('change', async (e) => {
  selectedFarmerId = e.target.value;
  updateTotalAcres();
  await loadFieldsForFarmer(selectedFarmerId);
});

map.on(L.Draw.Event.CREATED, async (event) => {
  if (!selectedFarmerId) return setStatus(fieldStatus, 'Select a farmer first.');
  const layer = event.layer;
  drawnItems.addLayer(layer);
  try {
    const payload = {
      name: fieldNameInput.value || 'New Field',
      notes: fieldNotesInput.value,
      geometry: layer.toGeoJSON().geometry,
    };
    const field = await fetchJson(`/api/farmers/${selectedFarmerId}/fields`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    layer.fieldId = field.id;
    layer.bindPopup(`<strong>${field.name}</strong><br/>${field.acres} acres`);
    layer.openPopup();
    setStatus(fieldStatus, 'Field saved.', true);
    await loadFarmers();
  } catch (err) {
    drawnItems.removeLayer(layer);
    setStatus(fieldStatus, err.message);
  }
});

map.on(L.Draw.Event.EDITED, async (event) => {
  const updates = [];
  event.layers.eachLayer((layer) => {
    if (!layer.fieldId) return;
    const payload = {
      name: fieldNameInput.value || 'Updated Field',
      notes: fieldNotesInput.value,
      geometry: layer.toGeoJSON().geometry,
    };
    updates.push(fetchJson(`/api/farmers/${selectedFarmerId}/fields/${layer.fieldId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }).then((field) => {
      layer.bindPopup(`<strong>${field.name}</strong><br/>${field.acres} acres`);
    }));
  });
  try {
    await Promise.all(updates);
    setStatus(fieldStatus, 'Fields updated.', true);
    await loadFarmers();
  } catch (err) {
    setStatus(fieldStatus, err.message);
  }
});

map.on(L.Draw.Event.DELETED, async (event) => {
  const deletions = [];
  event.layers.eachLayer((layer) => {
    if (!layer.fieldId) return;
    deletions.push(fetchJson(`/api/farmers/${selectedFarmerId}/fields/${layer.fieldId}`, { method: 'DELETE' }));
  });
  try {
    await Promise.all(deletions);
    setStatus(fieldStatus, 'Field removed.', true);
    await loadFarmers();
  } catch (err) {
    setStatus(fieldStatus, err.message);
  }
});

loadFarmers();
