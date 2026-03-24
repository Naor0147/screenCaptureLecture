import cv2
import numpy as np
import os
import time
import mss
import platform
import subprocess
from datetime import datetime

# --- GLOBAL CONFIGURATION (Default Settings) ---
CONFIG = {
    "CAPTURE_INTERVAL_SEC": 60,      # Check every 60 seconds
    "SECTION_INTERVAL_MIN": 120,      # Create new folder every 120 mins
    "PNG_COMPRESSION": 2,            # 0 (Fastest/Big) to 9 (Slowest/Small)
    "CHANGE_THRESHOLD": 2.0,         # Sensitivity for duplicate detection
    "SCREEN_INDEX": 2                # Monitor index for live capture (1-based)
}
# -----------------------------------------------

def get_unique_folder(path):
    """If folder exists, adds _v2, _v3, etc. to avoid overwriting."""
    if not os.path.exists(path):
        os.makedirs(path)
        return path
    
    counter = 2
    while True:
        new_path = f"{path}_v{counter}"
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            return new_path
        counter += 1

def ensure_subfolder_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def open_file_explorer(path):
    """Opens the folder in Windows Explorer (or Finder/Nautilus)."""
    try:
        path = os.path.abspath(path)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        print(f"Opened folder: {path}")
    except Exception as e:
        print(f"Could not open folder automatically: {e}")

def format_time_readable(seconds=None):
    if seconds is None:
        return datetime.now().strftime("%Hh-%Mm-%Ss")
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}h-{int(m):02d}m-{int(s):02d}s"

def detect_change(img1, img2):
    if img1 is None: return True
    diff = cv2.absdiff(img1, img2)
    score = (np.sum(diff) / (img1.shape[0] * img1.shape[1]))
    return score > CONFIG["CHANGE_THRESHOLD"]

def enhance_image(gray_img):
    """Applies adaptive thresholding + Invert (Dark Mode)."""
    clean = cv2.adaptiveThreshold(
        gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 10
    )
    return cv2.bitwise_not(clean)

def get_subfolder_name(minutes_elapsed):
    interval = CONFIG["SECTION_INTERVAL_MIN"]
    folder_index = int(minutes_elapsed // interval)
    start_min = folder_index * interval
    end_min = (folder_index + 1) * interval
    return f"Section_{folder_index + 1:02d}__Mins_{start_min}_to_{end_min}"

def list_monitors_info():
    """Returns list of available monitors (excluding the virtual 'all monitors')."""
    with mss.mss() as sct:
        return sct.monitors[1:]

def get_valid_screen_index(screen_index, monitor_count):
    """Clamps selected screen index to an existing monitor index."""
    if monitor_count <= 0:
        return 1
    if screen_index < 1:
        return 1
    if screen_index > monitor_count:
        return monitor_count
    return screen_index

def save_frame_based_on_mode(save_mode, gray_frame, base_section_path, timestamp):
    """
    Saves image(s) based on mode.
    If Mode 1 (Both), creates specific subfolders 'Gray' and 'Dark'.
    """
    comp_level = CONFIG["PNG_COMPRESSION"]
    saved_files_msg = []

    # MODE 1: SAVE BOTH (Separate Folders)
    if save_mode == '1':
        # Create separate paths
        path_gray_folder = os.path.join(base_section_path, "Gray")
        path_dark_folder = os.path.join(base_section_path, "Dark")
        ensure_subfolder_exists(path_gray_folder)
        ensure_subfolder_exists(path_dark_folder)

        # Save Gray
        filename_g = f"Slide_at_{timestamp}.png"
        cv2.imwrite(os.path.join(path_gray_folder, filename_g), gray_frame, [cv2.IMWRITE_PNG_COMPRESSION, comp_level])
        
        # Save Dark
        dark_frame = enhance_image(gray_frame)
        filename_d = f"Slide_at_{timestamp}.png"
        cv2.imwrite(os.path.join(path_dark_folder, filename_d), dark_frame, [cv2.IMWRITE_PNG_COMPRESSION, comp_level])
        
        saved_files_msg.append(f"Saved to /Gray & /Dark folders at {timestamp}")

    # MODE 2: GRAY ONLY
    elif save_mode == '2':
        filename = f"Slide_at_{timestamp}.png"
        full_path = os.path.join(base_section_path, filename)
        cv2.imwrite(full_path, gray_frame, [cv2.IMWRITE_PNG_COMPRESSION, comp_level])
        saved_files_msg.append(f"Saved Gray: {filename}")

    # MODE 3: DARK ONLY
    else:
        dark_frame = enhance_image(gray_frame)
        filename = f"Slide_at_{timestamp}.png"
        full_path = os.path.join(base_section_path, filename)
        cv2.imwrite(full_path, dark_frame, [cv2.IMWRITE_PNG_COMPRESSION, comp_level])
        saved_files_msg.append(f"Saved Dark: {filename}")

    return saved_files_msg

# ===========================
# SETTINGS MENU
# ===========================
def run_settings_menu():
    while True:
        print("\n========================================")
        print("          SETTINGS CONFIGURATION        ")
        print("========================================")
        print(f" [1] Capture Interval:   {CONFIG['CAPTURE_INTERVAL_SEC']} sec")
        print(f" [2] Section Duration:   {CONFIG['SECTION_INTERVAL_MIN']} min")
        print(f" [3] PNG Compression:    {CONFIG['PNG_COMPRESSION']} (0-9)")
        print(f" [4] Screen Index:       {CONFIG['SCREEN_INDEX']}")
        print(" [5] Back to Main Menu")
        print("========================================")
        
        choice = input("Select setting to change: ").strip()
        
        if choice == '1':
            try:
                val = int(input("Enter new interval (seconds): "))
                if val > 0: CONFIG['CAPTURE_INTERVAL_SEC'] = val
            except ValueError: print("Invalid number.")
            
        elif choice == '2':
            try:
                val = int(input("Enter new section duration (minutes): "))
                if val > 0: CONFIG['SECTION_INTERVAL_MIN'] = val
            except ValueError: print("Invalid number.")

        elif choice == '3':
            try:
                val = int(input("Enter compression (0=Fast/Big, 9=Slow/Small): "))
                if 0 <= val <= 9: CONFIG['PNG_COMPRESSION'] = val
            except ValueError: print("Invalid number (must be 0-9).")

        elif choice == '4':
            try:
                monitors = list_monitors_info()
                if not monitors:
                    print("No monitors detected.")
                    continue

                print("\nAvailable screens:")
                for idx, mon in enumerate(monitors, start=1):
                    print(f" [{idx}] {mon['width']}x{mon['height']} at ({mon['left']}, {mon['top']})")

                val = int(input("Choose screen index: "))
                if 1 <= val <= len(monitors):
                    CONFIG['SCREEN_INDEX'] = val
                else:
                    print(f"Invalid screen index. Enter 1 to {len(monitors)}.")
            except ValueError:
                print("Invalid number.")
            except Exception as e:
                print(f"Could not read monitors: {e}")
            
        elif choice == '5' or choice == '':
            break

# ===========================
# MODE 1: LIVE SCREEN CAPTURE
# ===========================
def run_live_capture(save_mode):
    print(f"\n--- LIVE MONITORING ACTIVE ---")
    print(f"Interval: {CONFIG['CAPTURE_INTERVAL_SEC']}s | Section: {CONFIG['SECTION_INTERVAL_MIN']}m")
    print(f"Press Ctrl+C to stop.\n")

    start_time = time.time()
    
    date_str = datetime.now().strftime("%Y-%m-%d__%H-%M")
    raw_path = os.path.join("Lecture_Screenshots", f"Live_Session_{date_str}")
    base_folder = get_unique_folder(raw_path) 

    last_saved_frame = None

    with mss.mss() as sct:
        monitor_count = len(sct.monitors) - 1
        selected_index = get_valid_screen_index(CONFIG['SCREEN_INDEX'], monitor_count)
        if selected_index != CONFIG['SCREEN_INDEX']:
            print(f"Requested screen {CONFIG['SCREEN_INDEX']} is unavailable. Using screen {selected_index} instead.")

        monitor = sct.monitors[selected_index]
        print(f"Targeting Screen #{selected_index}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")

        try:
            while True:
                elapsed_minutes = (time.time() - start_time) / 60
                subfolder = get_subfolder_name(elapsed_minutes)
                current_path = os.path.join(base_folder, subfolder)
                ensure_subfolder_exists(current_path)

                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                if detect_change(last_saved_frame, gray_frame):
                    timestamp = format_time_readable()
                    msgs = save_frame_based_on_mode(save_mode, gray_frame, current_path, timestamp)
                    for m in msgs: print(f"[SAVED] {m}")
                    last_saved_frame = gray_frame
                else:
                    print(f"[SKIPPED] No change.")

                time.sleep(CONFIG['CAPTURE_INTERVAL_SEC'])

        except KeyboardInterrupt:
            print("\n--- STOPPED ---")
            open_file_explorer(base_folder)

# ===========================
# MODE 2: VIDEO FILE PROCESS
# ===========================
def run_video_process(save_mode):
    video_path = input("\n>> Drag and drop video file: ").strip().replace('"', '').replace("'", "")

    if not os.path.exists(video_path):
        print("Error: File not found.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return

    fps = cap.get(cv2.CAP_PROP_FPS)
    duration_sec = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
    print(f"Video loaded. Length: {duration_sec/60:.2f} minutes.")

    # Select Region
    print("Select area and press SPACE/ENTER.")
    ret, first_frame = cap.read()
    if not ret: return

    r = cv2.selectROI("Select Area", first_frame, fromCenter=False)
    cv2.destroyWindow("Select Area")
    x, y, w, h = int(r[0]), int(r[1]), int(r[2]), int(r[3])
    if w == 0 or h == 0: return

    # Setup Folder
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    base_folder = get_unique_folder(os.path.join("Processed_Lectures", video_name))
    print(f"Saving to: {base_folder}")

    current_sec = 0
    last_saved_frame = None
    processed_count = 0

    print(f"\nProcessing...")

    while current_sec < duration_sec:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(current_sec * fps))
        ret, frame = cap.read()
        if not ret: break

        cropped = frame[y:y+h, x:x+w]
        gray_frame = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

        current_min = current_sec / 60
        subfolder = get_subfolder_name(current_min)
        current_save_path = os.path.join(base_folder, subfolder)
        ensure_subfolder_exists(current_save_path)

        if detect_change(last_saved_frame, gray_frame):
            timestamp = format_time_readable(current_sec)
            save_frame_based_on_mode(save_mode, gray_frame, current_save_path, timestamp)
            last_saved_frame = gray_frame
            processed_count += 1
            print(f"Saved slide at video time: {current_min:.1f}m")
        
        current_sec += CONFIG['CAPTURE_INTERVAL_SEC']

    cap.release()
    print(f"\n--- DONE (Saved {processed_count} slides) ---")
    open_file_explorer(base_folder)

# ===========================
# MAIN MENU
# ===========================
def main():
    while True:
        print("\n========================================")
        print("   LECTURE CAPTURE v4.0 (Customizable)  ")
        print("========================================")
        print(" [1] Live Screen Capture")
        print(" [2] Process a Video File")
        print(" [s] Settings (Interval, Size, Quality, Screen)")
        print("========================================")
        
        choice = input("Select option: ").strip().lower()
        
        

        if choice == 's':
            run_settings_menu()
            continue # Loop back to main menu after settings
        
        if choice in ['1', '2', '']:
            # Select Save Mode
            print("\n--- SELECT SAVE MODE ---")
            print(" [1] BOTH (Separate Folders for Gray/Dark)")
            print(" [2] GRAY Only")
            print(" [3] DARK Only (Inverted)")
            
            mode = input("Select mode (Default 2): ").strip()
            if mode not in ['1', '2', '3']: mode = '2'

            if choice == "2":
                run_video_process(mode)
            else:
                run_live_capture(mode)
            
            break # Exit loop after running task

if __name__ == "__main__":
    main()