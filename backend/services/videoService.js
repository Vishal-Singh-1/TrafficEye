const fs = require('fs');
const path = require('path');

// Stub: Returns sample data, replace with real video processing later
exports.getSampleTrafficData = () => {
  const dataPath = path.join(__dirname, '../data/sampleData.json');
  const raw = fs.readFileSync(dataPath);
  return JSON.parse(raw);
};

// Future: add actual video processing functions here