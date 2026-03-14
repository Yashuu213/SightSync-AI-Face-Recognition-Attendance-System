import cv2
import face_recognition
import numpy as np
import sys

def test_on_file(file_path):
    print(f"Testing on {file_path}")
    img = cv2.imread(file_path)
    if img is None:
        print("Failed to load image.")
        return
    
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"Shape: {rgb_img.shape}, Type: {rgb_img.dtype}")
    
    try:
        locations = face_recognition.face_locations(rgb_img)
        print(f"Found {len(locations)} faces.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_on_file(sys.argv[1])
    else:
        print("Please provide an image path.")
