import streamlit as st
import cv2
import numpy as np
import tempfile
import time
from ultralytics import YOLO

# Page config
st.set_page_config(page_title="Smart Traffic Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .metric-card {
        background-color: #1E2329;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #333;
        min-height: 180px;
    }
    .status-green { color: #00FF00; font-weight: bold; font-size: 1.2em;}
    .status-red { color: #FF0000; font-weight: bold; font-size: 1.2em;}
    .status-yellow { color: #FFFF00; font-weight: bold; font-size: 1.2em;}
    .video-container { border: 2px solid #555; border-radius: 8px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

class TrafficLogic:
    def __init__(self):
        self.t_min = 10
        self.t_max = 60
        self.t_car = 2
        
    def calculate_green_time(self, num_cars):
        if num_cars == 0:
            return 0 
        t_calculated = self.t_min + (num_cars * self.t_car)
        return min(max(t_calculated, self.t_min), self.t_max)

@st.cache_resource
def load_yolo_model():
    return YOLO("yolov8n.pt")

def init_session_state():
    if 'system_active' not in st.session_state:
        st.session_state.system_active = False
    if 'emergency_lane' not in st.session_state:
        st.session_state.emergency_lane = None
    if 'current_green_lane' not in st.session_state:
        st.session_state.current_green_lane = "Lane 1 (North)"

def draw_control_panel(logic_engine, current_counts):
    """Draws the central logic control panel"""
    st.subheader("💡 Intersection Brain")
    
    if st.session_state.emergency_lane:
        st.error(f"🚨 ACTIVE OVERRIDE: {st.session_state.emergency_lane} has Priority Right-of-Way!")
        st.session_state.current_green_lane = st.session_state.emergency_lane
    
    cols = st.columns(4)
    lanes = list(current_counts.keys())
    
    for i, lane in enumerate(lanes):
        cars = current_counts[lane]
        
        if lane == st.session_state.current_green_lane:
            status_html = '<span class="status-green">🟢 GREEN</span>'
            time_alloc = logic_engine.calculate_green_time(cars)
            time_disp = f"Dynamic Phase: {time_alloc}s"
        else:
            status_html = '<span class="status-red">🔴 RED</span>'
            if st.session_state.emergency_lane:
                time_disp = "Waiting for Emergency Clearance..."
            else:
                time_disp = "Waiting for rotation..."
                
        html = f"""
        <div class="metric-card">
            <h4>{lane}</h4>
            <h2 style="margin: 10px 0;">{cars} Cars</h2>
            <p style="margin-bottom: 5px;">{status_html}</p>
            <small style="color: #aaa;">{time_disp}</small>
        </div>
        """
        cols[i].markdown(html, unsafe_allow_html=True)
            
    st.divider()
    st.markdown("#### Manual Emergency Override")
    e_cols = st.columns(4)
    if e_cols[0].button("🚑 Lane 1 Alert", use_container_width=True): st.session_state.emergency_lane = "Lane 1 (North)"
    if e_cols[1].button("🚑 Lane 2 Alert", use_container_width=True): st.session_state.emergency_lane = "Lane 2 (South)"
    if e_cols[2].button("🚑 Lane 3 Alert", use_container_width=True): st.session_state.emergency_lane = "Lane 3 (East)"
    if e_cols[3].button("🚑 Lane 4 Alert", use_container_width=True): st.session_state.emergency_lane = "Lane 4 (West)"
    
    if st.session_state.emergency_lane:
        if st.button("✅ Resolve Emergency & Resume Cycle", type="primary", use_container_width=True):
            st.session_state.emergency_lane = None

def process_frame(frame, model, target_classes):
    """Detects vehicles in a single frame and returns the count and annotated frame"""
    if frame is None:
        return 0, None
        
    frame = cv2.resize(frame, (640, 480)) # Resize for dashboard fit
    count = 0
    results = model(frame, conf=0.35, verbose=False)
    
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) in target_classes:
                count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0, 255, 0), 2)
                
    # Convert for Streamlit
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Draw Count
    cv2.putText(frame_rgb, f"Count: {count}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
    
    return count, frame_rgb

def run_streamlit_app():
    init_session_state()
    st.title("🚦 Multi-Stream Smart Traffic Simulator")
    st.write("Upload 4 separate MP4 videos representing 4 different roads meeting at a junction. The AI will analyze all 4 feeds simultaneously and calculate the required traffic light logic.")
    
    logic_engine = TrafficLogic()
    model = load_yolo_model()
    target_classes = [2, 3, 5, 7] # vehicles
    
    # Upload Section
    st.subheader("1. Video Input Sources")
    upload_cols = st.columns(4)
    file_l1 = upload_cols[0].file_uploader("Lane 1 (North)", type=['mp4', 'mov', 'avi'])
    file_l2 = upload_cols[1].file_uploader("Lane 2 (South)", type=['mp4', 'mov', 'avi'])
    file_l3 = upload_cols[2].file_uploader("Lane 3 (East)", type=['mp4', 'mov', 'avi'])
    file_l4 = upload_cols[3].file_uploader("Lane 4 (West)", type=['mp4', 'mov', 'avi'])
    
    lanes_data = {
        "Lane 1 (North)": {"file": file_l1, "cap": None, "placeholder": upload_cols[0].empty()},
        "Lane 2 (South)": {"file": file_l2, "cap": None, "placeholder": upload_cols[1].empty()},
        "Lane 3 (East)": {"file": file_l3, "cap": None, "placeholder": upload_cols[2].empty()},
        "Lane 4 (West)": {"file": file_l4, "cap": None, "placeholder": upload_cols[3].empty()}
    }
    
    st.divider()

    # System Controls
    control_col1, control_col2 = st.columns([1, 4])
    if control_col1.button("▶️ START SIMULATION", type="primary", use_container_width=True):
        if not all([file_l1, file_l2, file_l3, file_l4]):
            st.warning("⚠️ Please upload a video file for all 4 lanes to run the full simulation.")
        else:
            st.session_state.system_active = True
            
    if control_col2.button("⏹️ STOP", use_container_width=False):
        st.session_state.system_active = False

    # The Control Panel (Middle)
    panel_placeholder = st.empty()
    
    # Main Simulation Loop
    if st.session_state.system_active:
        # Save temp files and initialize VideoCaptures
        for lane, data in lanes_data.items():
            if data["file"] is not None:
                tfile = tempfile.NamedTemporaryFile(delete=False) 
                tfile.write(data["file"].read())
                data["cap"] = cv2.VideoCapture(tfile.name)
        
        cycle_counter = 0
        cycle_length = 30 # switch lanes every 30 frames for demo pacing
        lane_list = list(lanes_data.keys())
        
        # Stop button at bottom to break loop easily
        stop_btn = st.button("Emergency Stop Simulation")
        
        # Continuous Processing
        while not stop_btn and st.session_state.system_active:
            current_counts = {}
            
            # Read 1 frame from all 4 videos
            for lane, data in lanes_data.items():
                if data["cap"] is not None:
                    ret, frame = data["cap"].read()
                    
                    if not ret:
                        # Video ended, loop back to start
                        data["cap"].set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = data["cap"].read()
                        
                    # AI Processing
                    count, frame_rgb = process_frame(frame, model, target_classes)
                    current_counts[lane] = count
                    
                    # Update Streamlit UI Video box
                    data["placeholder"].image(frame_rgb, use_container_width=True)
                else:
                    current_counts[lane] = 0
            
            # Update Simulation Brain Phase Rotation
            if not st.session_state.emergency_lane:
                cycle_counter += 1
                if cycle_counter > cycle_length:
                    cycle_counter = 0
                    idx = lane_list.index(st.session_state.current_green_lane)
                    next_idx = (idx + 1) % len(lane_list)
                    st.session_state.current_green_lane = lane_list[next_idx]

            # Redraw Control Panel with new data
            with panel_placeholder.container():
                draw_control_panel(logic_engine, current_counts)
                
            # Prevent Streamlit UI from locking up entirely
            time.sleep(0.01)

if __name__ == "__main__":
    run_streamlit_app()
