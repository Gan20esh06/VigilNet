"""
GPU Optimization & Benchmarking Module

Configures and optimizes YOLO for GPU inference, with benchmarking
capabilities to compare CPU vs GPU performance.
"""

import cv2
import numpy as np
import time
import torch
import psutil
import json
import os
from datetime import datetime
from typing import Dict, Tuple, Optional, Any
from ultralytics import YOLO


class PerformanceMetrics:
    """Container for performance metrics."""
    
    def __init__(self):
        self.inference_times = []
        self.memory_usage = []
        self.gpu_memory = []
        self.cpu_percent = []
        self.fps_values = []
    
    def add_inference(self, time_ms: float, mem_mb: float, gpu_mem: Optional[float] = None, cpu_pct: float = 0):
        """Record inference metrics."""
        self.inference_times.append(time_ms)
        self.memory_usage.append(mem_mb)
        if gpu_mem is not None:
            self.gpu_memory.append(gpu_mem)
        self.cpu_percent.append(cpu_pct)
    
    def add_fps(self, fps: float):
        """Record FPS."""
        self.fps_values.append(fps)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        def calc_stats(data):
            if not data:
                return None
            return {
                'mean': np.mean(data),
                'median': np.median(data),
                'min': np.min(data),
                'max': np.max(data),
                'std': np.std(data)
            }
        
        return {
            'inference_time_ms': calc_stats(self.inference_times),
            'memory_mb': calc_stats(self.memory_usage),
            'gpu_memory_mb': calc_stats(self.gpu_memory) if self.gpu_memory else None,
            'cpu_percent': calc_stats(self.cpu_percent),
            'fps': calc_stats(self.fps_values)
        }
    
    def print_summary(self):
        """Print summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("PERFORMANCE METRICS SUMMARY")
        print("="*60)
        
        if summary['inference_time_ms']:
            t_stats = summary['inference_time_ms']
            print(f"\nInference Time (ms):")
            print(f"  Mean:   {t_stats['mean']:.2f}")
            print(f"  Median: {t_stats['median']:.2f}")
            print(f"  Range:  {t_stats['min']:.2f} - {t_stats['max']:.2f}")
        
        if summary['fps']:
            fps_stats = summary['fps']
            print(f"\nFrames Per Second (FPS):")
            print(f"  Mean:   {fps_stats['mean']:.2f}")
            print(f"  Median: {fps_stats['median']:.2f}")
            print(f"  Range:  {fps_stats['min']:.2f} - {fps_stats['max']:.2f}")
        
        if summary['memory_mb']:
            mem_stats = summary['memory_mb']
            print(f"\nMemory Usage (MB):")
            print(f"  Mean:   {mem_stats['mean']:.1f}")
            print(f"  Peak:   {mem_stats['max']:.1f}")
        
        if summary['gpu_memory_mb']:
            gpu_stats = summary['gpu_memory_mb']
            print(f"\nGPU Memory Usage (MB):")
            print(f"  Mean:   {gpu_stats['mean']:.1f}")
            print(f"  Peak:   {gpu_stats['max']:.1f}")
        
        if summary['cpu_percent']:
            cpu_stats = summary['cpu_percent']
            print(f"\nCPU Usage (%):")
            print(f"  Mean:   {cpu_stats['mean']:.1f}")
            print(f"  Peak:   {cpu_stats['max']:.1f}")
        
        print("="*60 + "\n")


class GPUOptimizer:
    """Handles GPU configuration and optimization."""
    
    @staticmethod
    def check_gpu_availability() -> Tuple[bool, str]:
        """Check if GPU is available."""
        if not torch.cuda.is_available():
            return False, "No GPU detected"
        
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        return True, f"{device_name} (Count: {device_count})"
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """Get detailed GPU information."""
        if not torch.cuda.is_available():
            return {'available': False}
        
        return {
            'available': True,
            'device_name': torch.cuda.get_device_name(0),
            'device_count': torch.cuda.device_count(),
            'cuda_version': torch.version.cuda,
            'cudnn_version': torch.backends.cudnn.version(),
            'total_memory_gb': torch.cuda.get_device_properties(0).total_memory / 1e9,
            'compute_capability': torch.cuda.get_device_properties(0).major
        }
    
    @staticmethod
    def get_gpu_memory_usage() -> float:
        """Get current GPU memory usage in MB."""
        if not torch.cuda.is_available():
            return 0.0
        return torch.cuda.memory_allocated() / 1e6
    
    @staticmethod
    def optimize_yolo_for_gpu(model: YOLO, device: str = 'cuda') -> YOLO:
        """
        Optimize YOLO model for GPU inference.
        
        Args:
            model: YOLO model instance
            device: Device to use ('cuda' or 'cpu')
            
        Returns:
            Optimized model
        """
        # Move model to device
        if torch.cuda.is_available() and device == 'cuda':
            model.to('cuda')
            # Enable TensorRT optimization if available
            try:
                # This could be extended with TensorRT export for further optimization
                print("✓ Model moved to GPU (CUDA)")
            except Exception as e:
                print(f"⚠️  GPU optimization: {e}")
        
        return model
    
    @staticmethod
    def empty_gpu_cache():
        """Clear GPU cache."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()


class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self, model_path: str = "yolov8s.pt", video_path: int = 0):
        """
        Initialize benchmark.
        
        Args:
            model_path: Path to YOLO model
            video_path: Video file path or camera index
        """
        self.model_path = model_path
        self.video_path = video_path
        self.cpu_metrics = PerformanceMetrics()
        self.gpu_metrics = PerformanceMetrics()
    
    def benchmark_on_device(self, device: str, num_frames: int = 100) -> Dict[str, Any]:
        """
        Benchmark inference on specific device.
        
        Args:
            device: 'cpu' or 'cuda'
            num_frames: Number of frames to benchmark
            
        Returns:
            Benchmark results
        """
        print(f"\n{'='*60}")
        print(f"Benchmarking on {device.upper()}")
        print(f"{'='*60}")
        
        # Load model
        model = YOLO(self.model_path)
        
        if device == 'cuda':
            if not torch.cuda.is_available():
                print("✗ GPU not available, skipping GPU benchmark")
                return None
            model.to('cuda')
            print("✓ Model loaded on GPU")
        else:
            model.to('cpu')
            print("✓ Model loaded on CPU")
        
        # Open video
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print("✗ Failed to open video source")
            cap.release()
            return None
        
        frames_processed = 0
        start_time = time.time()
        
        print(f"Processing {num_frames} frames...")
        
        # Warmup
        ret, frame = cap.read()
        if ret:
            with torch.no_grad():
                _ = model(frame, verbose=False)
        
        # Benchmark loop
        while frames_processed < num_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Record system metrics
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1e6  # MB
            cpu_pct = process.cpu_percent(interval=0.01)
            
            # Inference
            torch.cuda.synchronize() if device == 'cuda' else None
            t_start = time.time()
            
            with torch.no_grad():
                results = model(frame, verbose=False)
            
            torch.cuda.synchronize() if device == 'cuda' else None
            t_end = time.time()
            
            inference_time = (t_end - t_start) * 1000  # ms
            mem_after = process.memory_info().rss / 1e6  # MB
            
            # Record metrics
            metrics = self.gpu_metrics if device == 'cuda' else self.cpu_metrics
            
            gpu_mem = GPUOptimizer.get_gpu_memory_usage() if device == 'cuda' else None
            metrics.add_inference(inference_time, mem_after, gpu_mem, cpu_pct)
            
            fps = 1000.0 / inference_time if inference_time > 0 else 0
            metrics.add_fps(fps)
            
            frames_processed += 1
            
            if frames_processed % 10 == 0:
                print(f"  Processed {frames_processed}/{num_frames} frames "
                      f"({fps:.1f} FPS, {inference_time:.2f}ms)")
        
        cap.release()
        
        # Print results
        print(f"\n✓ Benchmark completed ({frames_processed} frames)")
        
        result = {
            'device': device,
            'frames_processed': frames_processed,
            'metrics': metrics.get_summary(),
            'total_time': time.time() - start_time
        }
        
        metrics.print_summary()
        
        return result
    
    def compare_devices(self, num_frames: int = 100) -> Dict[str, Any]:
        """
        Compare CPU vs GPU performance.
        
        Args:
            num_frames: Frames to benchmark
            
        Returns:
            Comparison results
        """
        print("\n" + "="*60)
        print("CPU vs GPU PERFORMANCE COMPARISON")
        print("="*60)
        
        # Check GPU availability
        gpu_available, gpu_info = GPUOptimizer.check_gpu_availability()
        if gpu_available:
            print(f"GPU Available: {gpu_info}")
        else:
            print(f"GPU Not Available: {gpu_info}")
        
        # CPU Benchmark
        cpu_result = self.benchmark_on_device('cpu', num_frames)
        
        # GPU Benchmark
        gpu_result = None
        if gpu_available:
            gpu_result = self.benchmark_on_device('cuda', num_frames)
        
        # Comparison
        comparison = {
            'cpu': cpu_result,
            'gpu': gpu_result,
            'timestamp': datetime.now().isoformat(),
            'model': self.model_path
        }
        
        if cpu_result and gpu_result:
            cpu_fps = cpu_result['metrics']['fps']['mean']
            gpu_fps = gpu_result['metrics']['fps']['mean']
            speedup = gpu_fps / cpu_fps if cpu_fps > 0 else 0
            
            cpu_mem = cpu_result['metrics']['memory_mb']['mean']
            gpu_mem = gpu_result['metrics']['gpu_memory_mb']['mean'] if gpu_result['metrics']['gpu_memory_mb'] else 0
            
            print("\n" + "="*60)
            print("COMPARISON SUMMARY")
            print("="*60)
            print(f"CPU FPS:          {cpu_fps:.2f}")
            print(f"GPU FPS:          {gpu_fps:.2f}")
            print(f"Speedup:          {speedup:.2f}x faster on GPU")
            print(f"CPU Memory (Mean): {cpu_mem:.1f} MB")
            print(f"GPU Memory (Mean): {gpu_mem:.1f} MB")
            print("="*60 + "\n")
            
            comparison['speedup'] = speedup
            comparison['summary'] = {
                'cpu_fps': round(cpu_fps, 2),
                'gpu_fps': round(gpu_fps, 2),
                'speedup': round(speedup, 2),
                'cpu_memory_mb': round(cpu_mem, 1),
                'gpu_memory_mb': round(gpu_mem, 1)
            }
        
        return comparison
    
    def save_benchmark_report(self, comparison: Dict, output_dir: str = "benchmarks") -> str:
        """Save benchmark report to JSON."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f"✓ Benchmark report saved: {filename}")
        return filename


class OptimizedYOLO:
    """Wrapper for YOLO model with automatic GPU optimization."""
    
    def __init__(self, model_path: str = "yolov8s.pt", use_gpu: bool = True):
        """
        Initialize optimized YOLO.
        
        Args:
            model_path: Path to model file
            use_gpu: Enable GPU if available
        """
        self.model_path = model_path
        self.use_gpu = use_gpu
        
        # Check GPU
        gpu_available, gpu_info = GPUOptimizer.check_gpu_availability()
        
        if use_gpu and gpu_available:
            print(f"✓ Using GPU: {gpu_info}")
            self.device = 'cuda'
        else:
            print("ℹ Using CPU for inference")
            self.device = 'cpu'
        
        # Load and optimize model
        self.model = YOLO(model_path)
        self.model = GPUOptimizer.optimize_yolo_for_gpu(self.model, self.device)
        
        print(f"✓ Model loaded: {model_path}")
    
    def predict(self, frame: np.ndarray, **kwargs) -> Any:
        """Run inference on frame."""
        with torch.no_grad():
            results = self.model(frame, **kwargs)
        return results
    
    def benchmark(self, video_path: int = 0, num_frames: int = 100) -> Dict:
        """Run benchmark."""
        benchmark = PerformanceBenchmark(self.model_path, video_path)
        return benchmark.compare_devices(num_frames)
    
    def clear_cache(self):
        """Clear GPU cache."""
        GPUOptimizer.empty_gpu_cache()
