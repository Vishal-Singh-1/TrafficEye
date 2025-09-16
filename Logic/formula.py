# -------------------------------
# Adaptive Traffic Light Controller (Improved)
# -------------------------------

# Default Constants
DEFAULT_STRAIGHT_SAT_RATE = 1800   # vehicles/hour per lane (e.g., 0.5 vehicles/second)
DEFAULT_TURN_SAT_RATE = 1200       # vehicles/hour per lane
BETA = 0.05                        # Weight for the non-linear waiting penalty
HYSTERESIS_FACTOR = 1.2            # Required score margin to switch (e.g., 20% higher)
MAX_COUNT_FOR_DIMINISHING_RETURNS = 20 # Cap for vehicle count contribution
MIN_GREEN_TIME = 5                 # seconds
MAX_GREEN_TIME = 30                # seconds

def compute_priority_score(count, wait_time, sat_rate, beta=BETA):
    """
    Computes the priority score for a single lane.
    Args:
        count: Number of vehicles in the lane.
        wait_time: Total waiting time (seconds) for the lane.
        sat_rate: Saturation flow rate (vehicles/hour) for this specific lane.
        beta: Tuning parameter for the waiting penalty.
    Returns:
        float: The calculated priority score.
    """
    # VEHICLE TERM: Estimate time to clear the current queue (with diminishing returns)
    effective_vehicle_count = min(count, MAX_COUNT_FOR_DIMINISHING_RETURNS)
    # Convert saturation rate from veh/h to veh/s, then find time to clear 'effective_vehicle_count'
    vehicle_term = effective_vehicle_count / (sat_rate / 3600) 

    # WAIT TERM: Apply a non-linear penalty for waiting (aggressive fairness)
    wait_term = (wait_time ** 1.5) * beta

    return vehicle_term + wait_term

def calculate_green_duration(vehicle_count, sat_rate):
    """
    Calculates how long the green light should be for a lane once it wins.
    Args:
        vehicle_count: Number of vehicles to clear.
        sat_rate: Saturation flow rate (veh/h) for the lane.
    Returns:
        int: Green light duration in seconds, bounded by min and max.
    """
    # Calculate estimated time needed, using the same logic as the vehicle term
    effective_count = min(vehicle_count, MAX_COUNT_FOR_DIMINISHING_RETURNS)
    estimated_time = effective_count / (sat_rate / 3600)
    
    # Ensure the time is within safe and practical limits
    bounded_time = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, estimated_time))
    return round(bounded_time)

def decide_green_lane(lanes, emergency_flags, current_green_index, hysteresis=HYSTERESIS_FACTOR):
    """
    Decides which lane should get the green signal next.
    Args:
        lanes: List of dictionaries with keys 'count', 'wait_time', 'sat_rate'.
        emergency_flags: List of booleans indicating if an emergency vehicle is present.
        current_green_index: The index of the lane that is currently green.
        hysteresis: Factor by which a challenger must beat the current score.
    Returns:
        tuple: (index_of_chosen_lane, green_light_duration)
    """

    # 1. EMERGENCY OVERRIDE: Absolute priority
    for i, is_emergency in enumerate(emergency_flags):
        if is_emergency:
            print(f"🚑 EMERGENCY OVERRIDE: Switching to Lane {i}")
            duration = calculate_green_duration(lanes[i]['count'], lanes[i]['sat_rate'])
            return i, duration

    # 2. COMPUTE SCORES for all lanes
    scores = []
    for i, lane in enumerate(lanes):
        score = compute_priority_score(lane['count'], lane['wait_time'], lane['sat_rate'])
        scores.append(score)
    
    # 3. FIND THE STRONGEST CHALLENGER (ignore current green for now)
    challenger_score = -1
    challenger_index = current_green_index # Default to current if no good challenger

    for i in range(len(scores)):
        if i != current_green_index: # Only look at non-green lanes
            if scores[i] > challenger_score:
                challenger_score = scores[i]
                challenger_index = i
            # Tie-breaker: if scores are equal, pick the one waiting longer.
            elif scores[i] == challenger_score and lanes[i]['wait_time'] > lanes[challenger_index]['wait_time']:
                challenger_index = i

    # 4. APPLY HYSTERESIS: Does the challenger significantly outperform the current green?
    current_score = scores[current_green_index]
    if challenger_score > current_score * hysteresis:
        print(f"🟢 SWITCHING: Lane {challenger_index} (Score: {challenger_score:.1f}) beats Lane {current_green_index} (Score: {current_score:.1f}) with hysteresis.")
        chosen_lane = challenger_index
    else:
        print(f"🟡 HOLDING: Lane {current_green_index} (Score: {current_score:.1f}) holds. Challenger Lane {challenger_index} (Score: {challenger_score:.1f}) did not exceed hysteresis threshold.")
        chosen_lane = current_green_index

    # 5. CALCULATE GREEN LIGHT DURATION for the chosen lane
    duration = calculate_green_duration(lanes[chosen_lane]['count'], lanes[chosen_lane]['sat_rate'])
    return chosen_lane, duration

# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    # Simulate a 4-way intersection
    lanes = [
        {"count": 12, "wait_time": 30, "sat_rate": DEFAULT_STRAIGHT_SAT_RATE}, # North Straight
        {"count": 8,  "wait_time": 45, "sat_rate": DEFAULT_STRAIGHT_SAT_RATE}, # South Straight
        {"count": 3,  "wait_time": 60, "sat_rate": DEFAULT_TURN_SAT_RATE},     # East Turn
        {"count": 2,  "wait_time": 20, "sat_rate": DEFAULT_TURN_SAT_RATE}      # West Turn
    ]
    
    emergency_flags = [False, False, False, False]
    current_green_index = 0  # North is currently green

    print("Calculating priority scores and decision...")
    for i, lane in enumerate(lanes):
        score = compute_priority_score(lane['count'], lane['wait_time'], lane['sat_rate'])
        print(f"Lane {i}: Count={lane['count']}, Wait={lane['wait_time']}s -> Score: {score:.1f}")

    next_green_index, green_duration = decide_green_lane(lanes, emergency_flags, current_green_index)
    
    print(f"\nDecision: Next green light is for Lane {next_green_index} for {green_duration} seconds.")