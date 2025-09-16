// Adapted formula logic in JS for demo purposes

function computePriorityScore(count, waitTime, satRate, beta = 0.05) {
  const effectiveCount = Math.min(count, 20);
  const vehicleTerm = effectiveCount / (satRate / 3600);
  const waitTerm = Math.pow(waitTime, 1.5) * beta;
  return vehicleTerm + waitTerm;
}

function calculateGreenDuration(vehicleCount, satRate) {
  const effectiveCount = Math.min(vehicleCount, 20);
  const estimated = effectiveCount / (satRate / 3600);
  return Math.round(Math.max(5, Math.min(30, estimated)));
}

function decideGreenLane(lanes, emergencyFlags, currentGreenIndex, hysteresis = 1.2) {
  for (let i = 0; i < emergencyFlags.length; ++i) {
    if (emergencyFlags[i]) {
      return {
        nextGreenLane: i,
        greenDuration: calculateGreenDuration(lanes[i].count, lanes[i].sat_rate),
        reason: "emergency"
      };
    }
  }
  const scores = lanes.map(lane => computePriorityScore(lane.count, lane.wait_time, lane.sat_rate));
  let challengerScore = -1;
  let challengerIndex = currentGreenIndex;
  for (let i = 0; i < scores.length; ++i) {
    if (i !== currentGreenIndex && (scores[i] > challengerScore ||
      (scores[i] === challengerScore && lanes[i].wait_time > lanes[challengerIndex].wait_time))) {
      challengerScore = scores[i];
      challengerIndex = i;
    }
  }
  const currentScore = scores[currentGreenIndex];
  const chosenLane = challengerScore > currentScore * hysteresis ? challengerIndex : currentGreenIndex;
  return {
    nextGreenLane: chosenLane,
    greenDuration: calculateGreenDuration(lanes[chosenLane].count, lanes[chosenLane].sat_rate),
    reason: "priority"
  };
}

module.exports = { decideGreenLane, calculateGreenDuration };