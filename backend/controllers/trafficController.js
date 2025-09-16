const { spawn } = require('child_process');
const path = require('path');

// GET /api/traffic-data
exports.getTrafficData = (req, res) => {
  res.json({ message: "Traffic data fetched successfully" });
};

// POST /api/traffic-data/signal-decision
exports.postSignalDecision = (req, res) => {
  const inputData = JSON.stringify({
    lanes: req.body.lanes,
    emergency_flags: req.body.emergency_flags,
    current_green_index: req.body.current_green_index
  });

  const formulaPath = path.join(__dirname, '../../Logic/formula.py');
  const python = spawn('python', [formulaPath, inputData]);

  let result = '';
  let error = '';

  python.stdout.on('data', data => result += data.toString());
  python.stderr.on('data', data => error += data.toString());

  python.on('close', code => {
    if (error) console.error("Python error:", error);

    if (code !== 0 || error) {
      return res.status(500).json({ error: error || "Python process exited with code " + code });
    }
    try {
      res.json(JSON.parse(result));
    } catch (e) {
      res.status(500).json({ error: 'Invalid JSON from Python', details: result });
    }
  });
};