const videoService = require('../services/videoService');

// Controller to handle traffic data API
exports.getTrafficData = (req, res) => {
  // For now, returns sample data from videoService
  const data = videoService.getSampleTrafficData();
  res.json(data);
};