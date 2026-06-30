import asyncio
import websockets
import json
import cv2
import datetime
import os
import numpy as np
import threading # <-- NEW: For the background video stream
import time

# --- CONFIGURATION ---
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000
CLIENT_ID = "pro_stitcher"
RTSP_URL = "rtsp://192.168.1.10:8554/cam1"

SAVE_DIR = "mission_data"
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# --- GLOBAL STATE ---
telemetry = {
    "lat": 0.0,
    "lon": 0.0,
    "heading": 0.0 
}

latest_frame = None
frame_lock = threading.Lock()

# --- 0. BACKGROUND VIDEO THREAD (The Zero-Latency Fix) ---
def capture_loop():
    global latest_frame
    print(f"🎥 Connecting to always-on video stream: {RTSP_URL}...")
    
    # Optional: Setting buffer size to 1 forces OpenCV to drop old frames and stay live
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if cap.isOpened():
        print("✅ RTSP Stream locked and buffering. Ready for instant capture.")

    while True:
        if not cap.isOpened():
            time.sleep(1)
            cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        ret, frame = cap.read()
        if ret:
            with frame_lock:
                latest_frame = frame.copy()
        else:
            print("⚠️ RTSP Stream lost. Reconnecting...")
            cap.release()

# Start the video grabber in the background immediately
threading.Thread(target=capture_loop, daemon=True).start()

# --- 1. PRO HUD OVERLAY (Only for Final Pano) ---
def add_hud_overlay(image):
    h, w = image.shape[:2]
    
    f_scale = w / 1200.0
    if f_scale < 0.4: f_scale = 0.4
    thick = max(1, int(f_scale * 2))
    pad = int(20 * f_scale)
    
    overlay = image.copy()
    
    # A. BOTTOM BAR
    bar_h = int(50 * f_scale)
    cv2.rectangle(overlay, (0, h-bar_h), (w, h), (10, 10, 10), -1)
    
    # GPS
    gps_txt = f"LAT {telemetry['lat']:.5f}  LON {telemetry['lon']:.5f}"
    cv2.putText(overlay, gps_txt, (pad, h - int(15*f_scale)), cv2.FONT_HERSHEY_SIMPLEX, f_scale*0.8, (100, 255, 255), thick, cv2.LINE_AA)

    # TIME
    ts = datetime.datetime.now().strftime("%H:%M:%S UTC")
    tsz, _ = cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, f_scale*0.8, thick)
    cv2.putText(overlay, ts, (w - tsz[0] - pad, h - int(15*f_scale)), cv2.FONT_HERSHEY_SIMPLEX, f_scale*0.8, (200, 200, 200), thick, cv2.LINE_AA)

    # B. COMPASS TAPE
    heading = int(telemetry['heading']) % 360
    comp_w = int(200 * f_scale)
    comp_h = int(30 * f_scale)
    cx = w // 2
    
    cv2.rectangle(overlay, (cx - comp_w//2, 0), (cx + comp_w//2, comp_h), (0,0,0), -1)
    hdg_txt = f"{heading:03d}° MAG"
    htsz, _ = cv2.getTextSize(hdg_txt, cv2.FONT_HERSHEY_SIMPLEX, f_scale, thick)
    cv2.putText(overlay, hdg_txt, (cx - htsz[0]//2, comp_h - int(8*f_scale)), cv2.FONT_HERSHEY_SIMPLEX, f_scale, (0, 255, 0), thick, cv2.LINE_AA)
    
    tri_pt = np.array([[cx, comp_h], [cx-5, comp_h+5], [cx+5, comp_h+5]], np.int32)
    cv2.fillPoly(overlay, [tri_pt], (0, 255, 0))

    cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
    return image

# --- 2. SMART CROP ---
def smart_crop_3x1(image):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    coords = cv2.findNonZero(thresh)
    if coords is not None:
        x, y, w_valid, h_valid = cv2.boundingRect(coords)
        image = image[y:y+h_valid, x:x+w_valid]
        h, w = image.shape[:2]

    target_h = int(w / 3)
    if h > target_h:
        center_y = h // 2
        start_y = max(0, center_y - target_h // 2)
        end_y = min(h, start_y + target_h)
        return image[start_y:end_y, :]
    return image

# --- 3. CORE LOGIC ---
def get_frame():
    # Instantaneous fetch from the background thread instead of opening the stream
    with frame_lock:
        if latest_frame is not None:
            return latest_frame.copy()
    return None

def process_stitch(images):
    print(f"🧩 Stitching {len(images)} Clean Frames...")
    
    stitcher = cv2.Stitcher_create(mode=1)
    status, pano = stitcher.stitch(images)

    if status == cv2.Stitcher_OK:
        pano_clean = smart_crop_3x1(pano)
        final_img = add_hud_overlay(pano_clean)
        
        ts = datetime.datetime.now().strftime("%H%M%S")
        fname = f"{SAVE_DIR}/PANO_{ts}_PRO.jpg"
        cv2.imwrite(fname, final_img)
        print(f"✅ SAVED PANORAMA: {fname}")
        return True
    else:
        print(f"❌ Stitch Failed: Err {status}")
        return False

async def start_service():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/{CLIENT_ID}"
    captured_queue = []
    
    print(f"📡 Pro Stitcher Connected to {SERVER_IP}")
    
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            try:
                data = json.loads(msg)
                
                # TELEMETRY UPDATE
                if data.get("topic") == "gps":
                    p = data.get("payload", {})
                    telemetry["lat"] = p.get("lat", 0.0)
                    telemetry["lon"] = p.get("lon", 0.0)
                    if "yaw" in p: telemetry["heading"] = p["yaw"]

                # SNAPSHOT TRIGGER
                if data.get("topic") == "snapshot":
                    print("📸 SNAPSHOT TRIGGERED!")
                    frame = await asyncio.to_thread(get_frame)
                    
                    if frame is not None:
                        ts = datetime.datetime.now().strftime("%H%M%S")
                        raw_name = f"{SAVE_DIR}/RAW_{ts}.jpg"
                        cv2.imwrite(raw_name, frame)
                        print(f"   Saved Clean: {raw_name}")
                        
                        captured_queue.append(frame)
                        print(f"   In Stitch Queue: {len(captured_queue)}/3")
                        
                        if len(captured_queue) >= 3:
                            await asyncio.to_thread(process_stitch, captured_queue)
                            captured_queue.clear()
                    else:
                        print("❌ Failed to grab frame! Stream might be down.")

            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(start_service())
    except KeyboardInterrupt: pass
