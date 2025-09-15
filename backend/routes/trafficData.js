const express = require('express');
const router = express.Router();
const trafficController = require('../controllers/trafficController');

// GET /api/traffic-data
router.get('/', trafficController.getTrafficData);

module.exports = router;