import time

class TrafficController:
    """
    A foundational simulation of a Smart Traffic Light controller.
    This logic handles dynamic proportional timing and emergency overrides.
    """
    def __init__(self):
        # Configuration Variables
        self.t_min = 10  # Minimum guaranteed green time in seconds
        self.t_max = 60  # Maximum allowed green time to prevent starving
        self.t_car = 2   # Estimated seconds required per car to cross
        
        # State of the 4-way intersection (Lanes 1-4)
        self.lanes = {
            1: {'cars_waiting': 0, 'light': 'RED'},
            2: {'cars_waiting': 0, 'light': 'RED'},
            3: {'cars_waiting': 0, 'light': 'RED'},
            4: {'cars_waiting': 0, 'light': 'RED'}
        }
    
    def calculate_green_time(self, num_cars):
        """
        Calculates optimal green time for a given number of cars.
        Formula: t_calculated = t_min + (num_cars * t_car)
        Limits: Bounded between t_min and t_max
        """
        t_calculated = self.t_min + (num_cars * self.t_car)
        return min(max(t_calculated, self.t_min), self.t_max)

    def set_all_red(self):
        """Safely transitions any active green lights to yellow, then to red."""
        print(">> Transitioning all lanes to RED clearance state...")
        for lane_id, lane_state in self.lanes.items():
            if lane_state['light'] == 'GREEN':
                self.lanes[lane_id]['light'] = 'YELLOW'
                print(f"   Lane {lane_id}: YELLOW")
                time.sleep(1) # Simulated yellow light time (1 sec for demo)
            
            self.lanes[lane_id]['light'] = 'RED'
        
        print(">> All lanes are now RED.")
        print("-" * 40)

    def emergency_override(self, approaching_lane_id):
        """
        Instantly clears intersection for an emergency vehicle.
        This simulates the immediate right-of-way protocol.
        """
        print(f"\n[ALERT] 🚑 EMERGENCY VEHICLE DETECTED APPROACHING IN LANE {approaching_lane_id}!")
        
        # 1. Safely stop all active traffic
        self.set_all_red()
        
        # 2. Grant right-of-way to the emergency vehicle
        self.lanes[approaching_lane_id]['light'] = 'GREEN'
        print(f"[EMERGENCY CLEARANCE] Lane {approaching_lane_id}: GREEN (Override Active)")
        print("Holding green state until emergency vehicle successfully passes...")
        
        # Simulate the vehicle driving through
        time.sleep(3) 
        
        # 3. Resume normal status
        print("[EMERGENCY CLEARED] Emergency vehicle passed safely. Reverting to normal cycle.\n")
        self.set_all_red()

    def run_normal_cycle(self):
        """
        Simulates one full rotation of the intersection's adaptive cycle.
        """
        print("\n--- Starting Normal Adaptive Traffic Cycle ---")
        for lane_id, data in self.lanes.items():
            cars = data['cars_waiting']
            
            # Scenario: "Ghost Town" approach - Skip empty lanes entirely
            if cars == 0:
                print(f"Skipping Lane {lane_id} -> 0 cars waiting.")
                continue
            
            # Transition to green for the current lane
            self.set_all_red()
            self.lanes[lane_id]['light'] = 'GREEN'
            
            # Calculate dynamic time
            green_time = self.calculate_green_time(cars)
            print(f"Lane {lane_id}: GREEN")
            print(f"   -> Serving {cars} vehicles.")
            if cars * self.t_car + self.t_min > self.t_max:
                print(f"   -> [WARNING] Heavy Traffic. Capped at max {self.t_max}s.")
            else:
                print(f"   -> Calculated dynamic duration: {green_time} seconds.")
            
            # Simulate the green phase
            # In an actual deployment, we would loop and check for a 'Gap-Out' here
            time.sleep(1) # Using 1 second just for fast console simulation
            
            # Traffic has passed
            self.lanes[lane_id]['cars_waiting'] = 0 
            print(f"   -> Lane {lane_id} traffic cleared.")

# ==========================================
# SIMULATION DEMO SCRIPT
# ==========================================
if __name__ == "__main__":
    controller = TrafficController()
    
    # ---------------------------------------------------------
    # Scenario 1: Adaptive Flow (Imbalanced Traffic)
    # ---------------------------------------------------------
    print("\n[SIMULATION] Loading traffic data from mock cameras...")
    controller.lanes[1]['cars_waiting'] = 12 # Normal traffic
    controller.lanes[2]['cars_waiting'] = 0  # Empty lane (should skip)
    controller.lanes[3]['cars_waiting'] = 3  # Light traffic
    controller.lanes[4]['cars_waiting'] = 35 # Heavy traffic (should hit time limit)
    
    # Run a normal intersection cycle
    controller.run_normal_cycle()
    
    # ---------------------------------------------------------
    # Scenario 2: Emergency Override Action
    # ---------------------------------------------------------
    print("\n[SIMULATION] Loading new traffic data...")
    controller.lanes[1]['cars_waiting'] = 20
    controller.lanes[2]['cars_waiting'] = 15
    controller.lanes[3]['cars_waiting'] = 5
    controller.lanes[4]['cars_waiting'] = 10
    
    print("\n[SIMULATION] Starting cycle, but an ambulance approaches mid-cycle...")
    # Cycle starts normally at Lane 1
    controller.set_all_red()
    controller.lanes[1]['light'] = 'GREEN'
    print("Lane 1: GREEN (Normal Operation)")
    time.sleep(1)
    
    # SUDDENLY: Ambulance detected in lane 4
    controller.emergency_override(approaching_lane_id=4)
    
    print("[SIMULATION] Intersection returned to normal state.")
