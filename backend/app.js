const express = require('express');
const app = express();
const trafficDataRoute = require('./routes/trafficData');

const cors = require('cors');
app.use(cors());

app.use(express.json());
app.use('/api/traffic-data', trafficDataRoute);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});