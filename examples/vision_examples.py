"""
Examples demonstrating Vision and ContourDetector functionalities.
"""

import cv2
from spiberry.app.vision import Vision, ContourDetector

# TODO: Add example images and update paths in the examples below.

# ============================================================================
# VISION (YOLO OBJECT DETECTION) EXAMPLES
# ============================================================================

def example_vision_basic():
    """Detect objects from an image file."""
    # Load image
    image = cv2.imread("path/to/image.jpg")
    
    # Initialize and detect
    vision = Vision(model_path="yolo26n.pt")
    detections = vision.detect_objects_from_image(image, "yolo26n")
    
    # Print results
    for detection in detections:
        print(f"Class {detection['class_id']}: {detection['confidence']:.2f}")
        print(f"  Box: {detection['xyxy']}")


def example_vision_with_visualization():
    """Detect objects and draw bounding boxes."""
    image = cv2.imread("path/to/image.jpg")
    vision = Vision(model_path="yolo26n.pt")
    detections = vision.detect_objects_from_image(image, "yolo26n")
    
    # Draw detections
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["xyxy"])
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{detection['class_id']}: {detection['confidence']:.2f}"
        cv2.putText(image, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.imwrite("detections.jpg", image)


def example_vision_live_detection():
    """Detect objects using camera (requires Raspberry Pi)."""
    vision = Vision(model_path="yolo26n.pt")
    
    # Captures image and detects objects
    detections, center_points = vision.find_objects("yolo26n")
    
    print(f"Found {len(detections)} objects")
    for detection, center in zip(detections, center_points):
        print(f"Class {detection['class_id']} at ({center[0]:.2f}, {center[1]:.2f})")

# ============================================================================
# CONTOUR DETECTOR (COLOR-BASED DETECTION) EXAMPLES
# ============================================================================

def example_contour_detector_basic():
    """Detect colored contours in an image."""
    image = cv2.imread("path/to/image.jpg")
    
    detector = ContourDetector()
    detections = detector.detect_contours(image)
    
    if detections:
        for color, area, cx, cy in detections:
            print(f"{color}: area={area}, center=({cx}, {cy})")


def example_contour_detector_with_filters():
    """Detect contours with size and count filters."""
    image = cv2.imread("path/to/image.jpg")
    
    detector = ContourDetector()
    filters = {
        "min_area": 100,
        "max_area": 10000,
        "n": 3,  # Get top 3 largest contours
    }
    
    detections = detector.detect_contours(image, filters=filters)
    print(f"Found {len(detections)} contours")


def example_contour_detector_live():
    """Detect contours from camera (requires Raspberry Pi)."""
    detector = ContourDetector()
    
    # Capture and detect
    image = detector.camera.take_picture()
    detections = detector.detect_contours(image)
    
    if detections:
        # Sort by distance to center
        sorted_detections = sorted(detections, 
                                  key=lambda d: detector.closeness_to_center(image, d))
        print(f"Closest object: {sorted_detections[0][0]}")


if __name__ == "__main__":
    print("Vision Examples - Uncomment the example you want to run\n")
    
    # Object Detection Examples
    # example_vision_basic()
    # example_vision_with_visualization()
    # example_vision_live_detection()
    
    # Contour Detection Examples
    # example_contour_detector_basic()
    # example_contour_detector_with_filters()
    # example_contour_detector_live()
