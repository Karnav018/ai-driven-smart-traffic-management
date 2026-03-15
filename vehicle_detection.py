import cv2
import numpy as np

# Note: You will need to install the ultralytics package to run this YOLOv8 model
# Run: pip install ultralytics opencv-python
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("\n[WARNING] 'ultralytics' library not found. Please run: pip install ultralytics\n")

class MultiLaneDetector:
    def __init__(self, video_source="sample_intersection.mp4"):
        """
        Initializes the YOLOv8 model for a 4-way intersection.
        """
        self.video_source = video_source
        
        if YOLO_AVAILABLE:
            print("[INFO] Loading YOLOv8 nano model...")
            self.model = YOLO("yolov8n.pt") 
            self.target_classes = [2, 3, 5, 7] # Cars, Motorcycles, Buses, Trucks
        
        # Define 4 Regions of Interest (ROI) for the intersection video
        # These polygons represent Lane 1, Lane 2, Lane 3, and Lane 4.
        self.lanes = {
            "Lane 1 (North)": {
                "polygon": np.array([[(400, 100), (550, 100), (450, 300), (250, 300)]], dtype=np.int32),
                "color": (0, 255, 0), # Green
                "count": 0
            },
            "Lane 2 (South)": {
                "polygon": np.array([[(650, 450), (900, 450), (800, 650), (500, 650)]], dtype=np.int32),
                "color": (255, 0, 0), # Blue
                "count": 0
            },
            "Lane 3 (East)": {
                "polygon": np.array([[(800, 200), (1100, 200), (1200, 350), (750, 350)]], dtype=np.int32),
                "color": (0, 255, 255), # Yellow
                "count": 0
            },
            "Lane 4 (West)": {
                "polygon": np.array([[(100, 350), (350, 350), (250, 500), (50, 500)]], dtype=np.int32),
                "color": (255, 0, 255), # Magenta
                "count": 0
            }
        }

    def process_video(self):
        if not YOLO_AVAILABLE:
            print("[ERROR] Cannot run detection without ultralytics model installed.")
            return

        # Use absolute path to ensure OpenCV finds the newly downloaded video
        cap = cv2.VideoCapture(f"/Users/karnav/Desktop/Projects/smarttrafic/{self.video_source}")
        
        if not cap.isOpened():
            print(f"[WARNING] Could not open {self.video_source}.")
            return

        print("[INFO] Starting 4-Way Intersection Video Stream...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video for testing
                continue
                
            frame = cv2.resize(frame, (1280, 720)) # Standard HD resolution
            
            # Reset lane counts for this frame
            for lane in self.lanes.values():
                lane["count"] = 0
            
            # Draw the 4 ROI Polygons
            for name, data in self.lanes.items():
                cv2.polylines(frame, [data["polygon"]], isClosed=True, color=data["color"], thickness=2)
            
            # Run YOLOv8 tracking
            results = self.model(frame, stream=True, conf=0.35, verbose=False)
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    
                    if class_id in self.target_classes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        
                        # Check which lane the vehicle is in
                        vehicle_counted = False
                        
                        for name, data in self.lanes.items():
                            inside_roi = cv2.pointPolygonTest(data["polygon"], (cx, cy), False)
                            
                            if inside_roi >= 0:
                                data["count"] += 1
                                cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
                                cv2.circle(frame, (cx, cy), 4, data["color"], -1)
                                vehicle_counted = True
                                break # A car can only be in one lane
                        
                        # If a car is moving through the middle of the intersection, ignore it for the cue count
                        if not vehicle_counted:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 1)

            # Display the real-time counts on the screen like a dashboard
            y_offset = 40
            cv2.rectangle(frame, (10, 10), (350, 180), (0, 0, 0), -1) # Dashboard background
            for name, data in self.lanes.items():
                text = f"{name}: {data['count']} cars"
                cv2.putText(frame, text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, data["color"], 2)
                y_offset += 35

            cv2.imshow("Smart Traffic - 4-Way AI Camera Feed", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("==============================================")
    print("  Smart Traffic AI - Multi-Lane Detection PoC")
    print("==============================================")
    detector = MultiLaneDetector(video_source="sample_intersection.mp4")
    detector.process_video()
