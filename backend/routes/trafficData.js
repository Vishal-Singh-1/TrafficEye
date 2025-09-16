const express = require('express');
const router = express.Router();
const trafficController = require('../controllers/trafficController');

// Existing routes
router.get('/', trafficController.getTrafficData);

// Add this POST route!
router.post('/signal-decision', trafficController.postSignalDecision);

module.exports = router;