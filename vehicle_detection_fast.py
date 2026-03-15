import cv2
import numpy as np

class FastVehicleDetector:
    def __init__(self, video_source="sample_traffic.mp4"):
        """
        Initializes a lightweight OpenCV background subtractor for vehicle detection.
        This does not require heavy AI models like YOLO, making it perfect for rapid prototyping.
        """
        self.video_source = video_source
        
        # Initialize OpenCV's built-in Background Subtractor
        # history=500, varThreshold=50, detectShadows=True
        self.object_detector = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50)

        # Region of Interest (ROI) polygon - "The Counting Zone"
        # Adjusted slightly higher for the sample video perspective
        self.roi_polygon = np.array([[(150, 200), (550, 200), (600, 350), (100, 350)]], dtype=np.int32)

    def process_video(self):
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            print(f"[WARNING] Could not open {self.video_source}. Disabling detection.")
            return

        print("[INFO] Starting Fast OpenCV Video Stream...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                continue
                
            # Resize frame
            frame = cv2.resize(frame, (800, 600))
            
            # The count for this specific frame
            current_vehicles = 0

            # 1. Apply mask to only look at our ROI
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [self.roi_polygon], 255)
            roi = cv2.bitwise_and(frame, frame, mask=mask)

            # 2. Extract moving objects
            # Apply the background subtractor to the ROI
            mask_diff = self.object_detector.apply(roi)
            
            # Remove shadows (gray pixels) and noise
            _, mask_diff = cv2.threshold(mask_diff, 254, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask_diff = cv2.morphologyEx(mask_diff, cv2.MORPH_OPEN, kernel)
            mask_diff = cv2.morphologyEx(mask_diff, cv2.MORPH_CLOSE, kernel)

            # 3. Find contours (the actual objects)
            contours, _ = cv2.findContours(mask_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                # Calculate area to ignore tiny noise (like a bird or leaf)
                area = cv2.contourArea(cnt)
                if area > 800: # Threshold for a "car"
                    current_vehicles += 1
                    
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Draw a red box around the detected moving vehicle
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                    # Draw center dot
                    cx = x + w // 2
                    cy = y + h // 2
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            # Draw the Counting Zone (Green line)
            cv2.polylines(frame, [self.roi_polygon], isClosed=True, color=(0, 255, 0), thickness=2)
            
            # Put Text on screen
            cv2.putText(frame, f"Vehicles in ROI: {current_vehicles}", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

            cv2.imshow("Smart Traffic - Fast CV Demo", frame)
            
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("==============================================")
    print("  Smart Traffic AI - Fast CV Prototype")
    print("==============================================")
    detector = FastVehicleDetector(video_source="sample_traffic.mp4")
    detector.process_video()
