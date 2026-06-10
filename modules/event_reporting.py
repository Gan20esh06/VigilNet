"""
Event Reporting Module

Generates detailed reports containing person details, event types,
timestamps, supporting image evidence, and action summaries.
"""

import cv2
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


class EventReport:
    """Represents a single detected event/violation."""
    
    def __init__(self, 
                 student_id: int,
                 event_type: str,
                 timestamp: datetime,
                 description: str,
                 confidence: float,
                 risk_score: int,
                 frame_image: Optional[Any] = None,
                 metadata: Optional[Dict] = None):
        """
        Initialize event report.
        
        Args:
            student_id: Student ID
            event_type: Type of event (e.g., "TALKING", "LOOKING_AWAY")
            timestamp: Event timestamp
            description: Human-readable description
            confidence: Confidence score (0-1)
            risk_score: Risk score (0-100)
            frame_image: Optional BGR frame for evidence
            metadata: Additional metadata
        """
        self.student_id = student_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.description = description
        self.confidence = confidence
        self.risk_score = risk_score
        self.frame_image = frame_image
        self.metadata = metadata or {}
        self.image_path = None
    
    def save_evidence(self, output_dir: str = "violations") -> bool:
        """Save event image as evidence."""
        if self.frame_image is None:
            return False
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = (f"{output_dir}/{self.event_type}_S{self.student_id}_"
                       f"{timestamp_str}.jpg")
            
            cv2.imwrite(filename, self.frame_image)
            self.image_path = filename
            return True
            
        except Exception as e:
            print(f"✗ Failed to save evidence: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'student_id': self.student_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'confidence': round(self.confidence, 3),
            'risk_score': self.risk_score,
            'image_path': self.image_path,
            'metadata': self.metadata
        }


class SessionReport:
    """Comprehensive session report with all events and statistics."""
    
    def __init__(self, session_id: str, proctor_name: str = "Unknown"):
        """
        Initialize session report.
        
        Args:
            session_id: Unique session identifier
            proctor_name: Name of the proctor
        """
        self.session_id = session_id
        self.proctor_name = proctor_name
        self.start_time = datetime.now()
        self.end_time = None
        
        self.events: List[EventReport] = []
        self.student_details: Dict[int, Dict] = {}
        self.statistics = {
            'total_events': 0,
            'by_type': {},
            'by_student': {},
            'high_risk_events': 0,
            'average_risk': 0.0
        }
    
    def add_event(self, event: EventReport) -> None:
        """Add event to report."""
        self.events.append(event)
        
        # Update statistics
        event_type = event.event_type
        self.statistics['by_type'][event_type] = (
            self.statistics['by_type'].get(event_type, 0) + 1
        )
        
        student_id = event.student_id
        if student_id not in self.statistics['by_student']:
            self.statistics['by_student'][student_id] = 0
        self.statistics['by_student'][student_id] += 1
        
        if event.risk_score >= 70:
            self.statistics['high_risk_events'] += 1
    
    def set_student_details(self, student_id: int, details: Dict) -> None:
        """Set student metadata."""
        self.student_details[student_id] = details
    
    def finalize(self) -> None:
        """Finalize report."""
        self.end_time = datetime.now()
        
        if self.events:
            total_risk = sum(e.risk_score for e in self.events)
            self.statistics['average_risk'] = round(
                total_risk / len(self.events), 2
            )
        
        self.statistics['total_events'] = len(self.events)
        self.statistics['duration_seconds'] = (
            self.end_time - self.start_time
        ).total_seconds()
    
    def generate_json_report(self, output_dir: str = "reports") -> str:
        """Generate JSON report file."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/report_{self.session_id}_{timestamp}.json"
        
        report_data = {
            'session_id': self.session_id,
            'proctor_name': self.proctor_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'statistics': self.statistics,
            'student_details': self.student_details,
            'events': [e.to_dict() for e in self.events]
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return filename
    
    def generate_html_report(self, output_dir: str = "reports") -> str:
        """Generate HTML report file with embedded images."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/report_{self.session_id}_{timestamp}.html"
        
        # Build HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Exam Proctoring Report - {self.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .stat-box {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-number {{ font-size: 28px; font-weight: bold; color: #2980b9; }}
        .stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; margin-top: 5px; }}
        .event {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
        .event.warning {{ border-left-color: #f39c12; }}
        .event.info {{ border-left-color: #3498db; }}
        .event-time {{ font-weight: bold; color: #2c3e50; }}
        .event-type {{ display: inline-block; background: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; margin: 0 5px; }}
        .confidence {{ color: #27ae60; font-weight: bold; }}
        .risk {{ color: #e74c3c; font-weight: bold; }}
        .event-image {{ max-width: 300px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .summary {{ background: #d5f4e6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .alert {{ background: #fadbd8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Exam Proctoring Report</h1>
        <p><strong>Session ID:</strong> {self.session_id}</p>
        <p><strong>Proctor:</strong> {self.proctor_name}</p>
        <p><strong>Date:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>📊 Summary Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{self.statistics.get('total_events', 0)}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{self.statistics.get('high_risk_events', 0)}</div>
                <div class="stat-label">High Risk Events</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(self.student_details)}</div>
                <div class="stat-label">Students Tracked</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{self.statistics.get('average_risk', 0):.0f}</div>
                <div class="stat-label">Avg Risk Score</div>
            </div>
        </div>
    </div>
"""
        
        # Event type breakdown
        if self.statistics.get('by_type'):
            html_content += """
    <div class="section">
        <h2>📈 Event Type Breakdown</h2>
        <table>
            <tr>
                <th>Event Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
            total = sum(self.statistics['by_type'].values())
            for event_type, count in sorted(self.statistics['by_type'].items(), key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                html_content += f"""            <tr>
                <td><span class="event-type">{event_type}</span></td>
                <td>{count}</td>
                <td>{pct:.1f}%</td>
            </tr>
"""
            html_content += """        </table>
    </div>
"""
        
        # Student breakdown
        if self.statistics.get('by_student'):
            html_content += """
    <div class="section">
        <h2>👥 Student Event Summary</h2>
        <table>
            <tr>
                <th>Student ID</th>
                <th>Total Events</th>
                <th>Risk Profile</th>
            </tr>
"""
            for student_id in sorted(self.statistics['by_student'].keys()):
                count = self.statistics['by_student'][student_id]
                risk_profile = "HIGH" if count >= 5 else "MEDIUM" if count >= 2 else "LOW"
                html_content += f"""            <tr>
                <td>S{student_id}</td>
                <td>{count}</td>
                <td>{risk_profile}</td>
            </tr>
"""
            html_content += """        </table>
    </div>
"""
        
        # Detailed events
        if self.events:
            html_content += """
    <div class="section">
        <h2>🔍 Detailed Event Log</h2>
"""
            for event in self.events:
                risk_class = "alert" if event.risk_score >= 70 else "warning" if event.risk_score >= 40 else "info"
                confidence_pct = int(event.confidence * 100)
                
                html_content += f"""
        <div class="event {risk_class}">
            <div>
                <span class="event-time">{event.timestamp.strftime('%H:%M:%S')}</span>
                <span class="event-type">{event.event_type}</span>
                <span>Student <strong>S{event.student_id}</strong></span>
            </div>
            <p>{event.description}</p>
            <div>
                <span class="confidence">Confidence: {confidence_pct}%</span> | 
                <span class="risk">Risk Score: {event.risk_score}/100</span>
            </div>
"""
                
                # Include image if available
                if event.image_path and os.path.exists(event.image_path):
                    try:
                        with open(event.image_path, 'rb') as img_file:
                            import base64
                            img_data = base64.b64encode(img_file.read()).decode()
                            html_content += f"""            <img src="data:image/jpeg;base64,{img_data}" class="event-image" alt="{event.event_type}">
"""
                    except Exception as e:
                        html_content += f"            <p><em>Image unavailable: {e}</em></p>\n"
                
                html_content += """        </div>
"""
            html_content += """    </div>
"""
        
        html_content += f"""
    <div class="footer">
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>VigilNet Exam Proctoring System</p>
    </div>
</body>
</html>"""
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_csv_report(self, output_dir: str = "reports") -> str:
        """Generate CSV report for spreadsheet analysis."""
        import csv
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/report_{self.session_id}_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'student_id', 'event_type', 'description',
                'confidence', 'risk_score', 'image_path'
            ])
            writer.writeheader()
            
            for event in self.events:
                writer.writerow({
                    'timestamp': event.timestamp.isoformat(),
                    'student_id': event.student_id,
                    'event_type': event.event_type,
                    'description': event.description,
                    'confidence': round(event.confidence, 3),
                    'risk_score': event.risk_score,
                    'image_path': event.image_path or ''
                })
        
        return filename
    
    def print_summary(self) -> None:
        """Print summary to console."""
        print("\n" + "="*70)
        print(f"SESSION REPORT: {self.session_id}")
        print("="*70)
        print(f"Proctor: {self.proctor_name}")
        print(f"Duration: {self.statistics.get('duration_seconds', 0):.0f} seconds")
        print(f"Total Events: {self.statistics.get('total_events', 0)}")
        print(f"High Risk Events: {self.statistics.get('high_risk_events', 0)}")
        print(f"Average Risk Score: {self.statistics.get('average_risk', 0):.1f}/100")
        print("\nEvent Type Breakdown:")
        for event_type, count in sorted(self.statistics.get('by_type', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"  • {event_type}: {count}")
        print("="*70 + "\n")


class ReportManager:
    """Manages report generation and storage."""
    
    def __init__(self, session_id: str, proctor_name: str = "Unknown"):
        """Initialize report manager."""
        self.session_report = SessionReport(session_id, proctor_name)
    
    def add_event(self, event: EventReport) -> None:
        """Add event to session report."""
        self.session_report.add_event(event)
    
    def finalize_and_generate_all(self, output_dir: str = "reports") -> Dict[str, str]:
        """Generate all report formats."""
        self.session_report.finalize()
        
        reports = {
            'json': self.session_report.generate_json_report(output_dir),
            'html': self.session_report.generate_html_report(output_dir),
            'csv': self.session_report.generate_csv_report(output_dir)
        }
        
        self.session_report.print_summary()
        
        return reports
