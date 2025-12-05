import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { v4 as uuidv4 } from 'uuid';
import { attachUser, authorize, hasPermission, permissions } from './auth.js';
import { addAuditEntry, getAuditEntries } from './audit.js';
import { farmers, fields, invoices, fieldEvents } from './data.js';

const app = express();
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));
app.use(attachUser);
app.use(express.static('public'));

app.get('/api/farmers', (_req, res) => {
  res.json(farmers);
});

app.get('/api/farmers/:farmerId/fields', authorize('field', 'read'), (req, res) => {
  const farmerId = req.params.farmerId;
  const farmerFields = fields.filter((f) => f.farmerId === farmerId);
  res.json(farmerFields);
});

app.patch('/api/fields/:fieldId', authorize('field', 'update'), (req, res) => {
  const field = fields.find((f) => f.id === req.params.fieldId);
  if (!field) {
    return res.status(404).json({ error: 'not_found', message: 'Field not found' });
  }
  const { crop, acres, soilType } = req.body;
  if (crop) field.crop = crop;
  if (acres) field.acres = acres;
  if (soilType) field.soilType = soilType;

  addAuditEntry({
    userId: req.user.id,
    action: 'field.update',
    entityType: 'field',
    entityId: field.id,
    details: { crop: field.crop, acres: field.acres, soilType: field.soilType },
  });
  res.json(field);
});

app.get('/api/farmers/:farmerId/invoices', authorize('invoice', 'read'), (req, res) => {
  const farmerId = req.params.farmerId;
  const farmerInvoices = invoices.filter((i) => i.farmerId === farmerId);
  res.json(farmerInvoices);
});

app.post('/api/farmers/:farmerId/invoices', authorize('invoice', 'update'), (req, res) => {
  const farmerId = req.params.farmerId;
  const { fieldId, amount } = req.body;
  const invoice = { id: uuidv4(), farmerId, fieldId, amount, status: 'unpaid' };
  invoices.push(invoice);
  addAuditEntry({
    userId: req.user.id,
    action: 'invoice.create',
    entityType: 'invoice',
    entityId: invoice.id,
    details: { farmerId, fieldId, amount, status: invoice.status },
  });
  res.status(201).json(invoice);
});

app.patch('/api/invoices/:invoiceId/pay', authorize('invoice', 'update'), (req, res) => {
  const invoice = invoices.find((inv) => inv.id === req.params.invoiceId);
  if (!invoice) {
    return res.status(404).json({ error: 'not_found', message: 'Invoice not found' });
  }
  invoice.status = 'paid';
  addAuditEntry({
    userId: req.user.id,
    action: 'invoice.pay',
    entityType: 'invoice',
    entityId: invoice.id,
    details: { farmerId: invoice.farmerId, fieldId: invoice.fieldId, status: invoice.status },
  });
  res.json(invoice);
});

app.get('/api/fields/:fieldId/events', authorize('event', 'read'), (req, res) => {
  const fieldId = req.params.fieldId;
  res.json(fieldEvents.filter((evt) => evt.fieldId === fieldId));
});

app.post('/api/fields/:fieldId/events', authorize('event', 'create'), (req, res) => {
  const fieldId = req.params.fieldId;
  const { message } = req.body;
  const event = { id: uuidv4(), fieldId, message, createdAt: new Date().toISOString() };
  fieldEvents.unshift(event);
  addAuditEntry({
    userId: req.user.id,
    action: 'event.create',
    entityType: 'field',
    entityId: fieldId,
    details: { message },
  });
  res.status(201).json(event);
});

app.get('/api/audit', (req, res) => {
  const { farmerId, fieldId } = req.query;
  res.json(getAuditEntries({ farmerId, fieldId }));
});

app.get('/api/permissions', (req, res) => {
  res.json({ role: req.user.role, permissions });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`FieldFlux server running on http://localhost:${PORT}`);
});
