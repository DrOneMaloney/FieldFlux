const auditLog = [];

export function addAuditEntry({ userId, action, entityType, entityId, details }) {
  const entry = {
    id: auditLog.length + 1,
    userId,
    action,
    entityType,
    entityId,
    details,
    timestamp: new Date().toISOString(),
  };
  auditLog.unshift(entry);
  return entry;
}

export function getAuditEntries({ farmerId, fieldId }) {
  return auditLog.filter((entry) => {
    if (fieldId && entry.entityType === 'field' && entry.entityId !== fieldId) {
      return false;
    }
    if (farmerId && entry.entityType === 'farmer' && entry.entityId !== farmerId) {
      return false;
    }
    if (farmerId && entry.entityType === 'invoice' && entry.details?.farmerId !== farmerId) {
      return false;
    }
    return true;
  });
}
