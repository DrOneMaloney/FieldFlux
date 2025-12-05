export const farmers = [
  { id: 'farmer-1', name: 'Prairie Acres' },
  { id: 'farmer-2', name: 'Green River Co-op' },
];

export const fields = [
  {
    id: 'field-1',
    farmerId: 'farmer-1',
    name: 'North 40',
    crop: 'Corn',
    acres: 120,
    soilType: 'Loam',
  },
  {
    id: 'field-2',
    farmerId: 'farmer-1',
    name: 'East Pivot',
    crop: 'Soybeans',
    acres: 95,
    soilType: 'Sandy loam',
  },
  {
    id: 'field-3',
    farmerId: 'farmer-2',
    name: 'River Bottom',
    crop: 'Wheat',
    acres: 130,
    soilType: 'Silty clay',
  },
];

export const invoices = [
  { id: 'inv-1', farmerId: 'farmer-1', fieldId: 'field-1', amount: 1200, status: 'unpaid' },
  { id: 'inv-2', farmerId: 'farmer-2', fieldId: 'field-3', amount: 950, status: 'paid' },
];

export const fieldEvents = [
  { id: 'evt-1', fieldId: 'field-1', message: 'Applied nitrogen at V6', createdAt: '2024-05-03T12:00:00Z' },
  { id: 'evt-2', fieldId: 'field-2', message: 'Scouted for aphids, none found', createdAt: '2024-05-06T09:30:00Z' },
];
