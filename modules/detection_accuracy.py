"""
Enhanced Detection Accuracy Module

Implements ensemble methods, improved confidence thresholding,
and advanced filtering to enhance detection accuracy.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import deque


class DetectionFilter:
    """Implements temporal and spatial filtering for improved accuracy."""
    
    def __init__(self, history_size: int = 5, iou_threshold: float = 0.5):
        """
        Initialize detection filter.
        
        Args:
            history_size: Number of frames to consider for temporal filtering
            iou_threshold: IoU threshold for matching detections
        """
        self.history_size = history_size
        self.iou_threshold = iou_threshold
        self.detection_history = {}  # {class_id: deque of detections}
    
    @staticmethod
    def compute_iou(box1: Tuple, box2: Tuple) -> float:
        """Compute IoU between two boxes."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        if inter == 0:
            return 0
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        
        return inter / union
    
    def temporal_smooth(self, detections: List[Dict]) -> List[Dict]:
        """
        Smooth detections over time to reduce jitter.
        
        Args:
            detections: List of detection dicts with 'bbox' and 'confidence'
            
        Returns:
            Filtered detections
        """
        result = []
        
        for det in detections:
            class_id = det.get('label', 'unknown')
            bbox = det['bbox']
            conf = det['confidence']
            
            # Initialize history for this class
            if class_id not in self.detection_history:
                self.detection_history[class_id] = deque(maxlen=self.history_size)
            
            # Add current detection
            self.detection_history[class_id].append({
                'bbox': bbox,
                'confidence': conf
            })
            
            # Compute average confidence over history
            confidences = [d['confidence'] for d in self.detection_history[class_id]]
            avg_confidence = np.mean(confidences)
            
            # Require consistent detection (most frames in history)
            detection_consistency = len(self.detection_history[class_id]) / self.history_size
            
            # Only accept if high average confidence and consistency
            if avg_confidence >= 0.7 and detection_consistency >= 0.6:
                result.append({
                    **det,
                    'confidence': avg_confidence,
                    'consistency': round(detection_consistency, 2)
                })
        
        return result
    
    def non_maximum_suppression(self, detections: List[Dict], 
                                iou_threshold: Optional[float] = None) -> List[Dict]:
        """
        Apply NMS to remove overlapping detections.
        
        Args:
            detections: List of detections
            iou_threshold: IoU threshold (uses default if None)
            
        Returns:
            NMS-filtered detections
        """
        if not detections:
            return []
        
        iou_threshold = iou_threshold or self.iou_threshold
        
        # Sort by confidence
        sorted_dets = sorted(detections, 
                            key=lambda x: x['confidence'], 
                            reverse=True)
        
        result = []
        
        for det in sorted_dets:
            # Check overlap with kept detections
            overlaps = [self.compute_iou(det['bbox'], d['bbox']) 
                       for d in result]
            
            # Keep if no significant overlap
            if not overlaps or max(overlaps) < iou_threshold:
                result.append(det)
        
        return result


class ConfidenceThresholdOptimizer:
    """Optimizes confidence thresholds based on performance data."""
    
    def __init__(self):
        self.class_stats = {}  # {class: {'tp': 0, 'fp': 0, 'fn': 0}}
    
    def update_stats(self, class_name: str, true_positive: bool, 
                    false_positive: bool, false_negative: bool):
        """Update classification statistics."""
        if class_name not in self.class_stats:
            self.class_stats[class_name] = {'tp': 0, 'fp': 0, 'fn': 0}
        
        if true_positive:
            self.class_stats[class_name]['tp'] += 1
        if false_positive:
            self.class_stats[class_name]['fp'] += 1
        if false_negative:
            self.class_stats[class_name]['fn'] += 1
    
    def get_optimal_thresholds(self) -> Dict[str, float]:
        """Compute optimal confidence thresholds based on precision/recall."""
        optimal = {}
        
        for class_name, stats in self.class_stats.items():
            tp = stats['tp']
            fp = stats['fp']
            fn = stats['fn']
            
            if tp + fp > 0:
                precision = tp / (tp + fp)
            else:
                precision = 0
            
            if tp + fn > 0:
                recall = tp / (tp + fn)
            else:
                recall = 0
            
            # F1 score
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0
            
            # Adaptive threshold: higher precision preference for security-critical
            if class_name in ['cell phone', 'weapon']:
                # For security-critical objects, prefer precision
                optimal[class_name] = max(0.75, precision)
            else:
                # Standard threshold
                optimal[class_name] = max(0.60, f1)
        
        return optimal


class EnsembleDetector:
    """Ensemble multiple detectors for improved accuracy."""
    
    def __init__(self, primary_model_path: str = "yolov8s.pt",
                 ensemble_model_path: Optional[str] = None):
        """
        Initialize ensemble detector.
        
        Args:
            primary_model_path: Primary YOLO model
            ensemble_model_path: Alternative model for ensemble
        """
        from ultralytics import YOLO
        
        self.primary = YOLO(primary_model_path)
        self.ensemble = None
        
        if ensemble_model_path:
            try:
                self.ensemble = YOLO(ensemble_model_path)
                print(f"✓ Ensemble model loaded: {ensemble_model_path}")
            except Exception as e:
                print(f"⚠️  Failed to load ensemble model: {e}")
    
    def detect(self, frame: np.ndarray, classes: Optional[List] = None) -> List[Dict]:
        """
        Run detection with primary model.
        
        Args:
            frame: Input frame
            classes: Class IDs to detect
            
        Returns:
            Detections
        """
        results = self.primary(frame, classes=classes, verbose=False)
        detections = []
        
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': conf,
                'class_id': cls_id,
                'model': 'primary'
            })
        
        return detections
    
    def detect_ensemble(self, frame: np.ndarray, 
                       classes: Optional[List] = None,
                       voting_threshold: float = 0.5) -> List[Dict]:
        """
        Run detection with ensemble voting.
        
        Args:
            frame: Input frame
            classes: Class IDs to detect
            voting_threshold: Fraction of models that must agree
            
        Returns:
            Ensemble-voted detections
        """
        if not self.ensemble:
            return self.detect(frame, classes)
        
        # Get detections from both models
        primary_dets = self.detect(frame, classes)
        
        ensemble_results = self.ensemble(frame, classes=classes, verbose=False)
        ensemble_dets = []
        
        for box in ensemble_results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            ensemble_dets.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': conf,
                'class_id': cls_id,
                'model': 'ensemble'
            })
        
        # Voting logic
        all_dets = primary_dets + ensemble_dets
        voted_dets = {}  # key: detection, value: vote count
        
        for det in all_dets:
            # Find matching detection
            found = False
            for voted_det in voted_dets:
                iou = self._compute_iou(det['bbox'], voted_det['bbox'])
                if iou > 0.5:  # Same detection
                    voted_dets[voted_det] += 1
                    # Average confidence
                    voted_det['confidence'] = (
                        voted_det['confidence'] + det['confidence']
                    ) / 2
                    found = True
                    break
            
            if not found:
                voted_dets[det] = 1
        
        # Filter by voting threshold
        result = [det for det, votes in voted_dets.items()
                 if votes / 2 >= voting_threshold]
        
        return result
    
    @staticmethod
    def _compute_iou(box1: Tuple, box2: Tuple) -> float:
        """Compute IoU."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        if inter == 0:
            return 0
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        return inter / (area1 + area2 - inter)


class AdaptiveConfidenceThreshold:
    """Dynamically adjusts confidence thresholds based on scene."""
    
    def __init__(self, base_threshold: float = 0.65):
        self.base_threshold = base_threshold
        self.illumination_level = 0.5  # 0-1
        self.motion_level = 0.5  # 0-1
    
    def analyze_scene(self, frame: np.ndarray):
        """Analyze scene to adjust thresholds."""
        # Illumination analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.illumination_level = np.mean(gray) / 255.0
        
        # Motion analysis (can be expanded)
        self.motion_level = 0.5  # Placeholder
    
    def get_threshold(self, class_name: str) -> float:
        """Get adaptive threshold for class."""
        # Base thresholds per class
        base = {
            'cell phone': 0.75,
            'laptop': 0.70,
            'book': 0.65,
            'person': 0.60,
        }
        
        threshold = base.get(class_name, self.base_threshold)
        
        # Adjust for illumination (lower threshold in dark scenes)
        if self.illumination_level < 0.3:
            threshold -= 0.10  # Lower threshold in dark
        elif self.illumination_level > 0.9:
            threshold -= 0.05  # Slightly lower in very bright
        
        # Clamp to valid range
        return max(0.40, min(0.95, threshold))
