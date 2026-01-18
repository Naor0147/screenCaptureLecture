import cv2
import numpy as np
import os
import time
import mss
from datetime import datetime

# --- CONFIGURATION ---
SAVE_PATH = "Lecture_Screenshots"
CAPTURE_INTERVAL_SEC = 60      # Check every 60 seconds
NEW_FOLDER_INTERVAL_MIN = 10   # Create new folder every 10 mins
CHANGE_THRESHOLD = 2.0         # 2.0 is a good balance for sensitivity
# ---------------------

def ensure_folder_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def detect_change(img1, img2):
    """Returns True if the screen has changed significantly."""
    if img1 is None: return True
    
    # Calculate difference
    diff = cv2.absdiff(img1, img2)
    score = (np.sum(diff) / (img1.shape[0] * img1.shape[1]))
    
    # print(f"Change Score: {score:.2f}") # Uncomment to see the numbers
    return score > CHANGE_THRESHOLD

def main():
    print(f"\n--- FULL SCREEN MODE ACTIVE ---")
    print(f"Monitoring your entire primary screen.")
    print(f"Duplicate Detection is ON.")
    print(f"Press Ctrl+C to stop.\n")

    start_time = time.time()
    
    # Create main folder
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    base_folder = os.path.join(SAVE_PATH, f"Lecture_{date_str}")
    ensure_folder_exists(base_folder)

    last_saved_frame = None

    with mss.mss() as sct:
        # Select the primary monitor (Monitor 1) automatically
        monitor = sct.monitors[2] 

        try:
            while True:
                # 1. Calculate Time & Folder Structure
                elapsed_minutes = (time.time() - start_time) / 60
                folder_index = int(elapsed_minutes // NEW_FOLDER_INTERVAL_MIN)
                start_min = folder_index * NEW_FOLDER_INTERVAL_MIN
                end_min = (folder_index + 1) * NEW_FOLDER_INTERVAL_MIN
                
                subfolder = f"Part_{folder_index + 1}__Min_{start_min}-{end_min}"
                current_path = os.path.join(base_folder, subfolder)
                ensure_folder_exists(current_path)

                # 2. Capture Entire Screen
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                
                # 3. Convert to Black & White (to save space)
                # Note: mss gives BGRA, we convert to Gray
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # 4. Check for Changes
                if detect_change(last_saved_frame, gray_frame):
                    timestamp = datetime.now().strftime("%H-%M-%S")
                    filename = f"full_screen_{timestamp}.jpg"
                    full_path = os.path.join(current_path, filename)
                    
                    # Save (Quality 50 is fine for full screen text)
                    cv2.imwrite(full_path, gray_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    print(f"[SAVED] {filename}")
                    
                    last_saved_frame = gray_frame
                else:
                    print(f"[SKIPPED] No significant change.")

                # 5. Wait
                time.sleep(CAPTURE_INTERVAL_SEC)

        except KeyboardInterrupt:
            print("\n--- STOPPED ---")
            print(f"Saved to: {base_folder}")

if __name__ == "__main__":
    main()