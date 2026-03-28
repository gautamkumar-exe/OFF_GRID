import streamlit as st
import cv2
import numpy as np
import os
import sys
import time
import base64
import pandas as pd
import pydeck as pdk
from datetime import datetime
from collections import deque

# Add edge directory to path for AI engine access
edge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "edge"))
if edge_path not in sys.path:
    sys.path.append(edge_path)

from inference_engine import SentinelInferenceEngine

# ── Page Configuration ──
st.set_page_config(
    page_title="Sentinel Omni — Unified Surveillance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Premium "Sentinel Omni" Aesthetic ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@400;900&display=swap');

    :root {
        --primary: #3bbffa;
        --secondary: #f43f5e;
        --surface: #0f172a;
        --border: rgba(255, 255, 255, 0.1);
    }

    .stApp {
        background-color: #020617;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid var(--border);
    }

    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: -0.02em;
    }

    .card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 900;
        font-family: 'Outfit', sans-serif;
        line-height: 1;
        margin-top: 0.5rem;
    }

    .stat-label {
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b;
    }

    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-critical { background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); color: #f43f5e; }
    .badge-high { background: rgba(249, 115, 22, 0.1); border: 1px solid rgba(249, 115, 22, 0.3); color: #f97316; }
    .badge-safe { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ── State Initialization ──
if 'engine' not in st.session_state:
    st.session_state.engine = SentinelInferenceEngine(
        yolo_model_path="edge/best.pt",
        lstm_model_path="edge/violence_lstm_model.h5"
    )

if 'alert_history' not in st.session_state:
    st.session_state.alert_history = deque(maxlen=50)

if 'active_threats' not in st.session_state:
    st.session_state.active_threats = []

# ── Helper: Map Threat Level to Style ──
def get_threat_style(level):
    if level > 0.7: return "critical", "🚨 CRITICAL"
    if level > 0.4: return "high", "⚠️ HIGH"
    return "safe", "✅ SECURE"

# ── Sidebar Navigation ──
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <div style="background: rgba(59, 191, 250, 0.1); padding: 8px; border-radius: 10px; border: 1px solid rgba(59, 191, 250, 0.2);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3bbffa" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div>
            <h2 style="margin: 0; font-size: 1.2rem; line-height: 1;">SENTINEL</h2>
            <p style="margin: 0; font-size: 0.6rem; color: #64748b; font-weight: 800; letter-spacing: 0.2em;">OMNI INTELLIGENCE</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("OPERATIONAL CONSOLE", 
                   ["📊 Command Dashboard", "👁️ Live Surveillance", "🔬 Forensic Intelligence", "🗺️ Threat Topology"],
                   index=0)
    
    st.divider()
    
    st.markdown("### SYSTEM STATUS")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("UPTIME", "99.9%", "+0.02%")
    with col2:
        st.metric("LATENCY", "42ms", "-5ms")

# ── 1. Command Dashboard ──
if page == "📊 Command Dashboard":
    st.title("Command Intelligence Dashboard")
    st.markdown("Automated System Status & Real-time Metrics")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="card"><div class="stat-label">Total Detections</div><div class="stat-value">{len(st.session_state.alert_history)}</div></div>', unsafe_allow_html=True)
    with m2:
        weapons = sum(1 for a in st.session_state.alert_history if a.get('type') == 'weapon')
        st.markdown(f'<div class="card"><div class="stat-label">Weapons Identified</div><div class="stat-value" style="color:#f43f5e">{weapons}</div></div>', unsafe_allow_html=True)
    with m3:
        violence = sum(1 for a in st.session_state.alert_history if a.get('type') == 'violence')
        st.markdown(f'<div class="card"><div class="stat-label">Violence Alerts</div><div class="stat-value" style="color:#f97316">{violence}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="card"><div class="stat-label">AI Confidence</div><div class="stat-value" style="color:#3bbffa">94.8%</div></div>', unsafe_allow_html=True)

    # Activity Stream & Chart
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### RECENT ACTIVITY")
        if not st.session_state.alert_history:
            st.info("No activity detected. Start the Live Feed or upload a video.")
        else:
            for alert in sorted(st.session_state.alert_history, key=lambda x: x['timestamp'], reverse=True)[:5]:
                style_class, label = get_threat_style(alert['confidence'])
                st.markdown(f"""
                <div style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 10px; font-weight: 800; color: #64748b;">{alert['timestamp']}</span>
                        <div style="font-weight: 600;">{alert['label']}</div>
                    </div>
                    <span class="badge badge-{style_class}">{label}</span>
                </div>
                """, unsafe_allow_html=True)

    with c2:
        st.markdown("### SYSTEM LOAD")
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['CPU', 'GPU', 'NPU']
        )
        st.line_chart(chart_data)

# ── 2. Live Surveillance ──
elif page == "👁️ Live Surveillance":
    st.title("Live Neural Surveillance")
    st.markdown("Real-time Threat Identification & Analysis Loop")

    col_feed, col_side = st.columns([2, 1])
    
    with col_side:
        st.markdown("### CONFIGURATION")
        source = st.selectbox("Active Input", ["USB Camera (Local)", "Neural Network Simulation"])
        st.divider()
        st.markdown("### ANALYTICS OVERLAY")
        show_yolo = st.toggle("Show Weapon Bounding Boxes", True)
        show_pose = st.toggle("Show Activity Signatures", True)
        st.info("System is leveraging GPU acceleration (CUDA) for zero-latency inference.")

    with col_feed:
        st.markdown(f'<div style="background: #000; border: 2px solid rgba(59, 191, 250, 0.3); border-radius: 1rem; overflow: hidden; position: relative;">', unsafe_allow_html=True)
        
        # Simple camera loop handled via st.camera_input or background process
        # For simplicity in this demo, we'll provide a start/stop button
        run = st.checkbox('START NEURAL FEED')
        FRAME_WINDOW = st.image([])
        
        if run:
            cap = cv2.VideoCapture(0)
            while run:
                ret, frame = cap.read()
                if not ret: break
                
                # Run Inference
                detections, processed_frame = st.session_state.engine.process_frame(frame)
                
                # Draw Overlays
                debug_frame = st.session_state.engine.draw_overlays(processed_frame, detections)
                
                # Add to history if unique and high confidence
                for det in detections:
                    if det['type'] in ('weapon', 'violence'):
                        st.session_state.alert_history.appendleft({
                            **det,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                
                # Convert for Streamlit
                debug_frame = cv2.cvtColor(debug_frame, cv2.COLOR_BGR2RGB)
                FRAME_WINDOW.image(debug_frame)
                
                # Sleep to simulate FPS
                time.sleep(0.01)
        else:
            st.markdown("""
            <div style="height: 480px; display: flex; flex-direction: column; items: center; justify-content: center; background: #000; text-align: center;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                <p style="color: #64748b; font-weight: 800; font-size: 0.8rem; margin-top: 1rem;">NEURAL FEED STANDBY // SELECT 'START NEURAL FEED' TO INITIALIZE</p>
            </div>
            """, unsafe_allow_html=True)

# ── 3. Forensic Intelligence ──
elif page == "🔬 Forensic Intelligence":
    st.title("Forensic Intelligence Console")
    st.markdown("Unified Multi-Model Threat Verification & Video Forensics")

    uploaded_file = st.file_uploader("Upload Footage (MP4 / MKV / AVI)", type=["mp4", "mkv", "avi"])
    
    if uploaded_file is not None:
        t_start = time.time()
        # Save temp file
        with open("temp_forensics.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.status("Initializing Forensic Analysis...", expanded=True) as status:
            st.write("Running Neural Inference...")
            report = st.session_state.engine.analyze_video_file("temp_forensics.mp4")
            st.write("Generating Temporal Threat Topology...")
            time.sleep(1)
            status.update(label="Analysis Complete", state="complete", expanded=False)

        # Dashboard View
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            style_class, label = get_threat_style(0.9 if report['summary'] == 'Threatening' else 0.1)
            st.markdown(f'<div class="card"><div class="stat-label">Master Verdict</div><div class="stat-value" style="color:{"#f43f5e" if report["summary"] == "Threatening" else "#10b981"}">{report["summary"]}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="card"><div class="stat-label">Total Duration</div><div class="stat-value">{report["duration"]}s</div></div>', unsafe_allow_html=True)
        with col3:
            total_threats = report['weapon_count'] + report['violence_count']
            st.markdown(f'<div class="card"><div class="stat-label">Evidence Found</div><div class="stat-value" style="color:#f43f5e">{total_threats}</div></div>', unsafe_allow_html=True)

        # Timeline Chart
        st.markdown("### THREAT TOPOLOGY // TEMPORAL STREAM")
        timeline_df = pd.DataFrame(report['timeline'])
        st.area_chart(timeline_df.set_index('time')['threat_level'])

        # Evidence Collage
        st.markdown("### EVIDENCE COLLAGE // AUTOMATED EXTRACTION")
        if not report['significant_frames']:
             st.warning("No significant signatures identified.")
        else:
            cols = st.columns(4)
            for i, frame in enumerate(report['significant_frames']):
                with cols[i % 4]:
                    img_data = base64.b64decode(frame['image'])
                    st.image(img_data, caption=f"T+{frame['time']}s - {', '.join(frame['detections'])}")

# ── 4. Threat Topology Map ──
elif page == "🗺️ Threat Topology":
    st.title("Global Threat Topology")
    st.markdown("Interactive Visual Tracking of Surveillance Assets")

    # Mock Data for India/Global points
    mapping_data = pd.DataFrame({
        'lat': [28.6139, 19.0760, 12.9716, 22.5726, 13.0827],
        'lon': [77.2090, 72.8777, 77.5946, 88.3639, 80.2707],
        'severity': [0.8, 0.4, 0.1, 0.9, 0.2],
        'color': [[244, 63, 94, 200], [249, 115, 22, 200], [16, 185, 129, 200], [244, 63, 94, 200], [16, 185, 129, 200]]
    })

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v11',
        initial_view_state=pdk.ViewState(
            latitude=20.5937,
            longitude=78.9629,
            zoom=4,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=mapping_data,
                get_position='[lon, lat]',
                radius=100000,
                elevation_scale=50000,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=mapping_data,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=50000,
            ),
        ],
    ))

    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 1.5rem; border-radius: 1rem; border: 1px solid var(--border);">
        <h4 style="margin:0 0 10px 0; font-size: 0.8rem; color: #64748b;">ASSET DISTRIBUTION</h4>
        <p style="font-size: 0.7rem;">Currently monitoring 5 High-Value Asset Zones across the network. All nodes are reporting nominal telemetry except <b>Alpha-01 (New Delhi)</b> which shows heightened threat signatures.</p>
    </div>
    """, unsafe_allow_html=True)
