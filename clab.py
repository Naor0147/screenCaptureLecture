import pyautogui
import mss
import mss.tools
import time
import os

def main():
    print("--- CALIBRATION MODE ---")
    print("We will take multiple photos to find the perfect setting for your screen.")
    print("\n1. Open your video and pause it.")
    print("2. I will ask for the Top-Left and Bottom-Right of the whiteboard.")
    
    input("\nPress Enter when you are ready to start...")

    print("\nMove mouse to TOP-LEFT of the whiteboard...")
    time.sleep(3)
    x1, y1 = pyautogui.position()
    print(f"Captured Top-Left: {x1}, {y1}")

    print("\nMove mouse to BOTTOM-RIGHT of the whiteboard...")
    time.sleep(3)
    x2, y2 = pyautogui.position()
    print(f"Captured Bottom-Right: {x2}, {y2}")

    # Logical width/height (what Windows tells us)
    log_w = x2 - x1
    log_h = y2 - y1

    print("\nTaking test shots with different scales...")
    
    # Common Windows Display Scales
    scales_to_test = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5]

    with mss.mss() as sct:
        for scale in scales_to_test:
            try:
                # Apply the math
                region = {
                    "top": int(y1 * scale),
                    "left": int(x1 * scale),
                    "width": int(log_w * scale),
                    "height": int(log_h * scale)
                }

                # Capture
                img = sct.grab(region)
                filename = f"TEST_SCALE_{scale}.png"
                mss.tools.to_png(img.rgb, img.size, output=filename)
                print(f"Saved: {filename}")
            except Exception as e:
                print(f"Skipped scale {scale} (Error: {e})")

    print("\n--- DONE ---")
    print("Check your folder. Open the images named 'TEST_SCALE_...'.")
    print("Find the one that looks PERFECT (correct crop, no black bars).")
    print("Remember that number (e.g., 2.0 or 1.5).")

if __name__ == "__main__":
    main()