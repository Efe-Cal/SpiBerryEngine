import json
import os
from typing import Literal, TypedDict
import logging

import numpy as np
import cv2
from scipy.spatial import cKDTree

import importlib.util

from .camera import Camera

if importlib.util.find_spec("ultralytics") is not None:
    from ultralytics import YOLO

logger = logging.getLogger("SpiBerryEngine")

class Vision:
    def __init__(self, model_path="yolo26n.pt", camera:Camera=None):
        self.loaded_models = {}
        self.load_model(model_path)
        self.camera = camera if camera else Camera()
        
    def load_model(self, model):
        model_name = model.split(".")[0] 
        self.loaded_models[model_name] = YOLO(model)
        
    def detect_objects_from_image(self, image, model_name):
        model = self.loaded_models[model_name]
        results = model(image)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            xyxy = boxes.xyxy.cpu().tolist()
            confidences = boxes.conf.cpu().tolist() if boxes.conf is not None else [None] * len(xyxy)
            class_ids = boxes.cls.cpu().tolist() if boxes.cls is not None else [None] * len(xyxy)

            for bbox, confidence, class_id in zip(xyxy, confidences, class_ids):
                detections.append(
                    {
                        "xyxy": bbox,
                        "confidence": float(confidence) if confidence is not None else None,
                        "class_id": int(class_id) if class_id is not None else None,
                    }
                )

        return detections

    def find_objects(self, model_name):

        image = self.camera.take_picture()
        
        # Detect objects in the captured image
        detections = self.detect_objects_from_image(image, model_name)
        detected_objects = [detection["xyxy"] for detection in detections]
        
        center_points = []
        for obj in detected_objects:
            x1, y1, x2, y2 = obj
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            center_points.append((center_x / image.shape[1], center_y / image.shape[0]))
        
        return detections, center_points

class ContourDetector:
    MORPHOLOGY_KERNEL_SIZE = (7, 7)  # Kernel size for morphological operations
    DIST_TRESH = 0.4  # Distance threshold for distance transform
    EXTENSION_OFFSET = (10, 30, 30)  # Offset for extending color ranges
    FALLBACK_CONFIG = None # {"big_box_crop": [1735, 657, 172, 122], "color_ranges": {"red": [[[0, 143, 54], [12, 253, 164]], [[162, 143, 54], [179, 253, 164]]], "green": [[[60, 137, 13], [90, 247, 123]]], "blue": [[[94, 173, 45], [124, 255, 155]]], "yellow": [[[7, 170, 99], [37, 255, 209]]]}}
    
    def __init__(self, camera:Camera=None):
        self.camera = camera if camera else Camera()
        self.config = self.load_config()
    
    def closeness_to_center(self, img, detection):
        _,_,cx,cy = detection
        img_cx, img_cy = img.shape[1]//2, img.shape[0]//2
        return np.sqrt((cx - img_cx)**2 + (cy - img_cy)**2)
    
    @staticmethod
    def merge_close_contours(contours, d_thresh=20):
        """
        Merge contours whose minimum point-to-point distance <= d_thresh (pixels).
        Returns a list of merged contours (convex hulls).
        """
        if not contours:
            return []

        n = len(contours)

        # --- Union-Find ---
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            pa, pb = find(a), find(b)
            if pa != pb:
                parent[pb] = pa

        # --- Pre-compute reshaped point arrays and KD-trees once ---
        pts_list  = [c.reshape(-1, 2).astype(np.float32) for c in contours]
        trees     = [cKDTree(p) for p in pts_list]
        rects     = [cv2.boundingRect(c) for c in contours]

        # Inline bbox gap as a fast pre-filter (avoids a function-call per pair)
        def bbox_gap(r1, r2):
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2
            x_gap = max(0, max(x1, x2) - min(x1 + w1, x2 + w2))
            y_gap = max(0, max(y1, y2) - min(y1 + h1, y2 + h2))
            return x_gap, y_gap

        for i in range(n):
            for j in range(i + 1, n):
                xg, yg = bbox_gap(rects[i], rects[j])

                # Euclidean bbox gap is a lower-bound on true contour distance.
                # If it already exceeds threshold, skip exact check.
                if (xg * xg + yg * yg) > d_thresh * d_thresh:
                    continue

                # KD-tree query: for each point in the smaller contour,
                # find the nearest point in the larger one.
                if len(pts_list[i]) <= len(pts_list[j]):
                    min_dist = trees[j].query(pts_list[i], workers=1)[0].min()
                else:
                    min_dist = trees[i].query(pts_list[j], workers=1)[0].min()

                if min_dist <= d_thresh:
                    union(i, j)

        # --- Group and merge ---
        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)

        merged = []
        for idxs in groups.values():
            pts  = np.vstack([pts_list[k] for k in idxs])   # reuse pre-reshaped arrays
            hull = cv2.convexHull(pts.astype(np.int32))
            merged.append(hull)

        return merged

    def load_config(self):
        script_dir = os.path.dirname(__file__)
        config_path = os.path.join(script_dir, 'config.json')
        if not os.path.exists(config_path):
            logger.warning(f"[Vision] Configuration file not found at {config_path}. Using the hardcoded default configuration.")
            return self.FALLBACK_CONFIG
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config

    def build_clean_mask(self, hsv: np.ndarray,
                        ranges: list[tuple[list[int],tuple[int]]],
                        kernel_size: tuple[int,int]=MORPHOLOGY_KERNEL_SIZE) -> np.ndarray:
        """Build and clean mask for a list of HSV ranges."""
        mask = None
        for lo, hi in ranges:
            part = cv2.inRange(hsv, np.array(lo), np.array(hi))
            mask = part if mask is None else cv2.bitwise_or(mask, part)
        kernel = np.ones(kernel_size, np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def extend_color_range(self, color_range: list, offset:tuple=(5,10,10)) -> list:
        """Extends a color range by an offset."""
        if isinstance(color_range[0][0],list):
            lo = self.extend_color_range(color_range[0], offset)[0]
            hi = self.extend_color_range(color_range[1], offset)[0]
        else:
            lo, hi = color_range
            lo = list(max(0, c - o) for c, o in zip(lo, offset))
            hi = list(min(255, c + o) for c, o in zip(hi, offset))
            
        return [[lo, hi]]

    retry_with_extended = False
    
    class Filters(TypedDict):
        min_area: int
        max_area: int
        color: Literal["red", "green", "blue", "yellow"]
        n: int
        vertices: int
    
    def detect_contours(self, img, filters:Filters=None):
        """
        Detects contours in the image
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        detections = []
        for color, ranges in self.config["color_ranges"].items():
            # Create mask for the color
            mask = self.build_clean_mask(hsv, ranges, kernel_size=self.MORPHOLOGY_KERNEL_SIZE)

            dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            
            # Commenting out for now as it seems to be less effective than distance transform alone
            # ret, sure_fg = cv2.threshold(dist_transform,self.DIST_TRESH*dist_transform.max(),255,0)
            # sure_fg = sure_fg.astype(np.uint8) 
            
            # Find contours
            contours, _ = cv2.findContours(dist_transform.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Merge contours that are close to each other and calculate total area
            contours = self.merge_close_contours(contours, d_thresh=20)
                        
            if filters and filters["min_area"] is not None and filters["max_area"] is not None:
                contours = [c for c in contours if filters['min_area'] < cv2.contourArea(c) < filters['max_area']]
            
            if not contours:
                continue
            
            # Get the largest n contours
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            n = filters["n"] if filters else 1
            contours = sorted_contours[:n]
            
            for cnt in contours:
                M = cv2.moments(cnt)
                cx = int(M['m10'] / M['m00']) if M['m00'] > 0 else 0
                cy = int(M['m01'] / M['m00']) if M['m00'] > 0 else 0
            
                detections.append((color, cv2.contourArea(cnt), cx, cy))
            
        if len(detections) == 0 and self.retry_with_extended==False:
            logger.info("[Vision] No boxes detected")
            self.retry_with_extended = True
            return self.detect_contours(img, self.extend_color_range(self.config["color_ranges"]))
        if len(detections) == 0 and self.retry_with_extended==True:
            logger.info("[Vision] No boxes detected even after extending ranges")
            self.retry_with_extended = False
            return None
        
        return detections
    
    @staticmethod
    def crop_image(img, x:int, y:int, w:int, h:int) -> np.ndarray:
        return img[y:y+h, x:x+w]


if __name__ == "__main__":
    import cv2

    # Load an image from file
    image = cv2.imread(r"C:\Users\efeca\Desktop\dogs.jpg")

    # Detect objects in the image
    detected_objects = Vision().detect_objects_from_image(image, "yolo26n")

    # Show detected objects on the image
    for obj in detected_objects:
        x1, y1, x2, y2 = map(int, obj["xyxy"])  # Bounding box coordinates
        confidence = obj["confidence"] if obj["confidence"] is not None else 0.0
        class_id = obj["class_id"] if obj["class_id"] is not None else -1

        # Draw bounding box and label on the image
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"Class: {class_id}, Conf: {confidence:.2f}"
        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Display the image with detected objects
    cv2.imshow("Detected Objects", image)
    cv2.waitKey(0)