import cv2
import numpy as np
import os

# --- CONFIGURATION ---
CAPTURE_INTERVAL_SEC = 60         # Check video every 60 seconds
NEW_FOLDER_INTERVAL_MIN = 10      # New folder every 10 video-minutes
CHANGE_THRESHOLD = 2.0            # Duplicate detection sensitivity
# ---------------------

def ensure_folder_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def detect_change(img1, img2):
    """Returns True if the difference between images is significant."""
    if img1 is None: return True
    diff = cv2.absdiff(img1, img2)
    score = (np.sum(diff) / (img1.shape[0] * img1.shape[1]))
    return score > CHANGE_THRESHOLD

def format_time(seconds):
    """Converts seconds to HH-MM-SS string."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}-{int(m):02d}-{int(s):02d}"

def main():
    # 1. Get Video File
    video_path = input("Drag and drop your video file here and press Enter: ").strip()
    # Remove quotes if the OS added them (common when dragging files)
    video_path = video_path.replace('"', '').replace("'", "")

    if not os.path.exists(video_path):
        print("Error: File not found.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps
    print(f"Video loaded. Duration: {duration_sec/60:.2f} minutes.")

    # 2. Select Region of Interest (ROI)
    print("Reading first frame for selection...")
    ret, first_frame = cap.read()
    if not ret:
        print("Error: Cannot read video frame.")
        return

    print("\n--- INSTRUCTIONS ---")
    print("1. A window will open showing the first frame.")
    print("2. Click and drag to draw a box around the whiteboard.")
    print("3. Press ENTER or SPACE to confirm selection.")
    print("4. Press c to cancel.")
    
    # This opens the GUI to draw the box
    r = cv2.selectROI("Select Whiteboard", first_frame, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Select Whiteboard")
    
    # r is (x, y, w, h)
    x, y, w, h = int(r[0]), int(r[1]), int(r[2]), int(r[3])
    
    if w == 0 or h == 0:
        print("No region selected. Exiting.")
        return

    # 3. Setup Save Location
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    base_folder = os.path.join("Processed_Lectures", video_name)
    ensure_folder_exists(base_folder)

    # 4. Process Video
    current_sec = 0
    last_saved_frame = None
    processed_count = 0

    print(f"\nProcessing started... (Targeting {w}x{h} area)")

    while current_sec < duration_sec:
        # Jump to the specific second
        frame_id = int(current_sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        
        ret, frame = cap.read()
        if not ret:
            break

        # Crop to the selected whiteboard area
        cropped = frame[y:y+h, x:x+w]
        
        # Convert to Grayscale
        gray_frame = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

        # Folder Logic (e.g., 0-10 min, 10-20 min)
        current_min = current_sec / 60
        folder_index = int(current_min // NEW_FOLDER_INTERVAL_MIN)
        start_min = folder_index * NEW_FOLDER_INTERVAL_MIN
        end_min = (folder_index + 1) * NEW_FOLDER_INTERVAL_MIN
        
        subfolder_name = f"Part_{folder_index + 1}__Min_{start_min}-{end_min}"
        current_save_path = os.path.join(base_folder, subfolder_name)
        ensure_folder_exists(current_save_path)

        # Duplicate Check
        if detect_change(last_saved_frame, gray_frame):
            timestamp = format_time(current_sec)
            filename = f"board_{timestamp}.jpg"
            full_path = os.path.join(current_save_path, filename)
            
            cv2.imwrite(full_path, gray_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            last_saved_frame = gray_frame
            processed_count += 1
            print(f"Saved: {filename} (Time: {current_min:.1f}m)")
        
        current_sec += CAPTURE_INTERVAL_SEC

    cap.release()
    print(f"\n--- DONE ---")
    print(f"Saved {processed_count} images to: {base_folder}")

if __name__ == "__main__":
    main()