#!/usr/bin/env python3
"""
RAG Monitoring and Logging - Comprehensive monitoring for vector operations and system performance.

This module provides monitoring, logging, and analytics capabilities for the RAG-based
SQL system, including vector operation tracking, performance metrics, and alerting.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from threading import Lock
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorOperation:
    """Represents a vector operation for monitoring"""
    operation_id: str
    operation_type: str  # 'store', 'retrieve', 'search', 'update', 'delete'
    timestamp: datetime
    duration_ms: float
    vector_count: int
    success: bool
    error_message: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class QueryMetrics:
    """Metrics for query processing"""
    query_id: str
    natural_language_query: str
    timestamp: datetime
    processing_stages: Dict[str, float]  # Stage name -> duration in ms
    total_duration_ms: float
    success: bool
    confidence: float
    sql_generated: Optional[str]
    error_message: Optional[str]
    recovery_attempted: bool
    vector_operations: List[VectorOperation]


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_usage_mb: float
    vector_store_size: int
    active_connections: int
    cache_hit_rate: float
    average_response_time_ms: float


@dataclass
class PerformanceAlert:
    """Performance alert information"""
    alert_id: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    resolved: bool
    resolved_at: Optional[datetime]


class RAGMonitor:
    """
    Comprehensive monitoring system for RAG operations.
    
    Tracks vector operations, query performance, system metrics,
    and provides alerting capabilities.
    """
    
    def __init__(self, 
                 monitoring_dir: str = "monitoring",
                 max_metrics_history: int = 10000,
                 alert_thresholds: Dict[str, Any] = None):
        """
        Initialize RAG monitoring system.
        
        Args:
            monitoring_dir: Directory to store monitoring data
            max_metrics_history: Maximum number of metrics to keep in memory
            alert_thresholds: Custom alert thresholds
        """
        self.monitoring_dir = Path(monitoring_dir)
        self.monitoring_dir.mkdir(exist_ok=True)
        
        self.max_metrics_history = max_metrics_history
        self._lock = Lock()
        
        # Metrics storage
        self.vector_operations: deque = deque(maxlen=max_metrics_history)
        self.query_metrics: deque = deque(maxlen=max_metrics_history)
        self.system_metrics: deque = deque(maxlen=max_metrics_history)
        self.performance_alerts: List[PerformanceAlert] = []
        
        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        # Alert thresholds
        self.alert_thresholds = alert_thresholds or self._get_default_alert_thresholds()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        logger.info(f"RAG monitoring initialized - storing data in {monitoring_dir}")
    
    def _get_default_alert_thresholds(self) -> Dict[str, Any]:
        """Get default alert thresholds"""
        return {
            'cpu_usage_percent': {'high': 80, 'critical': 95},
            'memory_usage_mb': {'high': 2048, 'critical': 4096},
            'average_response_time_ms': {'high': 5000, 'critical': 10000},
            'error_rate_percent': {'medium': 10, 'high': 25, 'critical': 50},
            'vector_operation_failure_rate': {'medium': 5, 'high': 15, 'critical': 30}
        }
    
    def track_vector_operation(self, 
                              operation_type: str,
                              vector_count: int = 1,
                              metadata: Dict[str, Any] = None) -> 'VectorOperationTracker':
        """
        Create a context manager to track vector operations.
        
        Args:
            operation_type: Type of vector operation
            vector_count: Number of vectors involved
            metadata: Additional metadata
            
        Returns:
            VectorOperationTracker context manager
        """
        return VectorOperationTracker(self, operation_type, vector_count, metadata or {})
    
    def track_query_processing(self, 
                              natural_language_query: str,
                              metadata: Dict[str, Any] = None) -> 'QueryProcessingTracker':
        """
        Create a context manager to track query processing.
        
        Args:
            natural_language_query: The natural language query
            metadata: Additional metadata
            
        Returns:
            QueryProcessingTracker context manager
        """
        return QueryProcessingTracker(self, natural_language_query, metadata or {})
    
    def record_vector_operation(self, operation: VectorOperation):
        """Record a vector operation"""
        with self._lock:
            self.vector_operations.append(operation)
            
            # Update counters
            self.counters[f'vector_operations_{operation.operation_type}'] += 1
            if operation.success:
                self.counters[f'vector_operations_{operation.operation_type}_success'] += 1
            else:
                self.counters[f'vector_operations_{operation.operation_type}_failure'] += 1
            
            # Update timers
            self.timers[f'vector_operations_{operation.operation_type}_duration'].append(operation.duration_ms)
            
            # Check for alerts
            self._check_vector_operation_alerts()
    
    def record_query_metrics(self, metrics: QueryMetrics):
        """Record query processing metrics"""
        with self._lock:
            self.query_metrics.append(metrics)
            
            # Update counters
            self.counters['queries_total'] += 1
            if metrics.success:
                self.counters['queries_success'] += 1
            else:
                self.counters['queries_failure'] += 1
            
            if metrics.recovery_attempted:
                self.counters['queries_recovery_attempted'] += 1
            
            # Update timers
            self.timers['query_processing_duration'].append(metrics.total_duration_ms)
            self.timers['query_confidence'].append(metrics.confidence)
            
            # Check for alerts
            self._check_query_performance_alerts()
    
    def record_system_metrics(self):
        """Record current system metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory.used / (1024 * 1024),
                disk_usage_mb=disk.used / (1024 * 1024),
                vector_store_size=self.counters.get('vector_store_size', 0),
                active_connections=self.counters.get('active_connections', 0),
                cache_hit_rate=self._calculate_cache_hit_rate(),
                average_response_time_ms=self._calculate_average_response_time()
            )
            
            with self._lock:
                self.system_metrics.append(metrics)
            
            # Check for system alerts
            self._check_system_alerts(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = self.counters.get('cache_hits', 0)
        misses = self.counters.get('cache_misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time"""
        durations = self.timers.get('query_processing_duration', [])
        return sum(durations) / len(durations) if durations else 0.0
    
    def _check_vector_operation_alerts(self):
        """Check for vector operation performance alerts"""
        # Calculate failure rate for recent operations
        recent_ops = list(self.vector_operations)[-100:]  # Last 100 operations
        if len(recent_ops) < 10:  # Need minimum sample size
            return
        
        failure_count = sum(1 for op in recent_ops if not op.success)
        failure_rate = (failure_count / len(recent_ops)) * 100
        
        threshold = self.alert_thresholds['vector_operation_failure_rate']
        
        if failure_rate >= threshold['critical']:
            self._create_alert(
                'vector_operation_failure_rate',
                'critical',
                f'Vector operation failure rate is {failure_rate:.1f}% (critical threshold: {threshold["critical"]}%)',
                {'failure_rate': failure_rate, 'sample_size': len(recent_ops)}
            )
        elif failure_rate >= threshold['high']:
            self._create_alert(
                'vector_operation_failure_rate',
                'high',
                f'Vector operation failure rate is {failure_rate:.1f}% (high threshold: {threshold["high"]}%)',
                {'failure_rate': failure_rate, 'sample_size': len(recent_ops)}
            )
    
    def _check_query_performance_alerts(self):
        """Check for query performance alerts"""
        recent_queries = list(self.query_metrics)[-50:]  # Last 50 queries
        if len(recent_queries) < 5:
            return
        
        # Check error rate
        error_count = sum(1 for q in recent_queries if not q.success)
        error_rate = (error_count / len(recent_queries)) * 100
        
        threshold = self.alert_thresholds['error_rate_percent']
        
        if error_rate >= threshold['critical']:
            self._create_alert(
                'query_error_rate',
                'critical',
                f'Query error rate is {error_rate:.1f}% (critical threshold: {threshold["critical"]}%)',
                {'error_rate': error_rate, 'sample_size': len(recent_queries)}
            )
        elif error_rate >= threshold['high']:
            self._create_alert(
                'query_error_rate',
                'high',
                f'Query error rate is {error_rate:.1f}% (high threshold: {threshold["high"]}%)',
                {'error_rate': error_rate, 'sample_size': len(recent_queries)}
            )
        
        # Check average response time
        avg_response_time = sum(q.total_duration_ms for q in recent_queries) / len(recent_queries)
        response_threshold = self.alert_thresholds['average_response_time_ms']
        
        if avg_response_time >= response_threshold['critical']:
            self._create_alert(
                'slow_query_performance',
                'critical',
                f'Average query response time is {avg_response_time:.1f}ms (critical threshold: {response_threshold["critical"]}ms)',
                {'average_response_time_ms': avg_response_time, 'sample_size': len(recent_queries)}
            )
        elif avg_response_time >= response_threshold['high']:
            self._create_alert(
                'slow_query_performance',
                'high',
                f'Average query response time is {avg_response_time:.1f}ms (high threshold: {response_threshold["high"]}ms)',
                {'average_response_time_ms': avg_response_time, 'sample_size': len(recent_queries)}
            )
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system-level alerts"""
        # CPU usage alert
        cpu_threshold = self.alert_thresholds['cpu_usage_percent']
        if metrics.cpu_usage_percent >= cpu_threshold['critical']:
            self._create_alert(
                'high_cpu_usage',
                'critical',
                f'CPU usage is {metrics.cpu_usage_percent:.1f}% (critical threshold: {cpu_threshold["critical"]}%)',
                {'cpu_usage_percent': metrics.cpu_usage_percent}
            )
        elif metrics.cpu_usage_percent >= cpu_threshold['high']:
            self._create_alert(
                'high_cpu_usage',
                'high',
                f'CPU usage is {metrics.cpu_usage_percent:.1f}% (high threshold: {cpu_threshold["high"]}%)',
                {'cpu_usage_percent': metrics.cpu_usage_percent}
            )
        
        # Memory usage alert
        memory_threshold = self.alert_thresholds['memory_usage_mb']
        if metrics.memory_usage_mb >= memory_threshold['critical']:
            self._create_alert(
                'high_memory_usage',
                'critical',
                f'Memory usage is {metrics.memory_usage_mb:.1f}MB (critical threshold: {memory_threshold["critical"]}MB)',
                {'memory_usage_mb': metrics.memory_usage_mb}
            )
        elif metrics.memory_usage_mb >= memory_threshold['high']:
            self._create_alert(
                'high_memory_usage',
                'high',
                f'Memory usage is {metrics.memory_usage_mb:.1f}MB (high threshold: {memory_threshold["high"]}MB)',
                {'memory_usage_mb': metrics.memory_usage_mb}
            )
    
    def _create_alert(self, alert_type: str, severity: str, message: str, metrics: Dict[str, Any]):
        """Create a performance alert"""
        alert = PerformanceAlert(
            alert_id=f"{alert_type}_{int(time.time())}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics,
            resolved=False,
            resolved_at=None
        )
        
        self.performance_alerts.append(alert)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"Performance alert created: {alert.severity.upper()} - {message}")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        for alert in self.performance_alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert_id}")
                break
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period.
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Performance summary dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_vector_ops = [op for op in self.vector_operations if op.timestamp >= cutoff_time]
        recent_queries = [q for q in self.query_metrics if q.timestamp >= cutoff_time]
        recent_system_metrics = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
        recent_alerts = [a for a in self.performance_alerts if a.timestamp >= cutoff_time]
        
        # Calculate summary statistics
        summary = {
            'time_period_hours': hours,
            'summary_generated_at': datetime.now().isoformat(),
            'vector_operations': {
                'total_operations': len(recent_vector_ops),
                'successful_operations': sum(1 for op in recent_vector_ops if op.success),
                'failed_operations': sum(1 for op in recent_vector_ops if not op.success),
                'average_duration_ms': sum(op.duration_ms for op in recent_vector_ops) / len(recent_vector_ops) if recent_vector_ops else 0,
                'operations_by_type': {}
            },
            'query_processing': {
                'total_queries': len(recent_queries),
                'successful_queries': sum(1 for q in recent_queries if q.success),
                'failed_queries': sum(1 for q in recent_queries if not q.success),
                'average_duration_ms': sum(q.total_duration_ms for q in recent_queries) / len(recent_queries) if recent_queries else 0,
                'average_confidence': sum(q.confidence for q in recent_queries) / len(recent_queries) if recent_queries else 0,
                'recovery_attempts': sum(1 for q in recent_queries if q.recovery_attempted)
            },
            'system_performance': {
                'average_cpu_usage': sum(m.cpu_usage_percent for m in recent_system_metrics) / len(recent_system_metrics) if recent_system_metrics else 0,
                'average_memory_usage_mb': sum(m.memory_usage_mb for m in recent_system_metrics) / len(recent_system_metrics) if recent_system_metrics else 0,
                'cache_hit_rate': self._calculate_cache_hit_rate()
            },
            'alerts': {
                'total_alerts': len(recent_alerts),
                'critical_alerts': sum(1 for a in recent_alerts if a.severity == 'critical'),
                'high_alerts': sum(1 for a in recent_alerts if a.severity == 'high'),
                'medium_alerts': sum(1 for a in recent_alerts if a.severity == 'medium'),
                'resolved_alerts': sum(1 for a in recent_alerts if a.resolved),
                'unresolved_alerts': sum(1 for a in recent_alerts if not a.resolved)
            }
        }
        
        # Operations by type
        for op in recent_vector_ops:
            op_type = op.operation_type
            if op_type not in summary['vector_operations']['operations_by_type']:
                summary['vector_operations']['operations_by_type'][op_type] = {
                    'count': 0,
                    'success_count': 0,
                    'average_duration_ms': 0
                }
            
            summary['vector_operations']['operations_by_type'][op_type]['count'] += 1
            if op.success:
                summary['vector_operations']['operations_by_type'][op_type]['success_count'] += 1
        
        # Calculate average durations by operation type
        for op_type in summary['vector_operations']['operations_by_type']:
            type_ops = [op for op in recent_vector_ops if op.operation_type == op_type]
            if type_ops:
                summary['vector_operations']['operations_by_type'][op_type]['average_duration_ms'] = sum(op.duration_ms for op in type_ops) / len(type_ops)
        
        return summary
    
    def export_metrics(self, output_file: str, format: str = 'json'):
        """
        Export metrics to file.
        
        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
        """
        try:
            if format.lower() == 'json':
                self._export_metrics_json(output_file)
            elif format.lower() == 'csv':
                self._export_metrics_csv(output_file)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Metrics exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise
    
    def _export_metrics_json(self, output_file: str):
        """Export metrics to JSON format"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'vector_operations': [asdict(op) for op in self.vector_operations],
            'query_metrics': [asdict(q) for q in self.query_metrics],
            'system_metrics': [asdict(m) for m in self.system_metrics],
            'performance_alerts': [asdict(a) for a in self.performance_alerts],
            'counters': dict(self.counters),
            'performance_summary': self.get_performance_summary()
        }
        
        # Convert datetime objects to ISO strings
        data = self._serialize_datetime_objects(data)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _export_metrics_csv(self, output_file: str):
        """Export metrics to CSV format"""
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write query metrics
            writer.writerow(['Query Metrics'])
            writer.writerow(['Query ID', 'Timestamp', 'Duration (ms)', 'Success', 'Confidence', 'Error'])
            
            for q in self.query_metrics:
                writer.writerow([
                    q.query_id,
                    q.timestamp.isoformat(),
                    q.total_duration_ms,
                    q.success,
                    q.confidence,
                    q.error_message or ''
                ])
            
            writer.writerow([])  # Empty row
            
            # Write vector operations
            writer.writerow(['Vector Operations'])
            writer.writerow(['Operation ID', 'Type', 'Timestamp', 'Duration (ms)', 'Success', 'Vector Count'])
            
            for op in self.vector_operations:
                writer.writerow([
                    op.operation_id,
                    op.operation_type,
                    op.timestamp.isoformat(),
                    op.duration_ms,
                    op.success,
                    op.vector_count
                ])
    
    def _serialize_datetime_objects(self, obj):
        """Recursively serialize datetime objects to ISO strings"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        else:
            return obj
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all unresolved alerts"""
        return [alert for alert in self.performance_alerts if not alert.resolved]
    
    def clear_old_metrics(self, days: int = 7):
        """Clear metrics older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            # Filter out old metrics
            self.vector_operations = deque(
                [op for op in self.vector_operations if op.timestamp >= cutoff_time],
                maxlen=self.max_metrics_history
            )
            
            self.query_metrics = deque(
                [q for q in self.query_metrics if q.timestamp >= cutoff_time],
                maxlen=self.max_metrics_history
            )
            
            self.system_metrics = deque(
                [m for m in self.system_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics_history
            )
            
            # Clear old alerts
            self.performance_alerts = [
                alert for alert in self.performance_alerts 
                if alert.timestamp >= cutoff_time or not alert.resolved
            ]
        
        logger.info(f"Cleared metrics older than {days} days")


class VectorOperationTracker:
    """Context manager for tracking vector operations"""
    
    def __init__(self, monitor: RAGMonitor, operation_type: str, vector_count: int, metadata: Dict[str, Any]):
        self.monitor = monitor
        self.operation_type = operation_type
        self.vector_count = vector_count
        self.metadata = metadata
        self.start_time = None
        self.operation_id = f"{operation_type}_{int(time.time() * 1000)}"
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        operation = VectorOperation(
            operation_id=self.operation_id,
            operation_type=self.operation_type,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            vector_count=self.vector_count,
            success=success,
            error_message=error_message,
            metadata=self.metadata
        )
        
        self.monitor.record_vector_operation(operation)


class QueryProcessingTracker:
    """Context manager for tracking query processing"""
    
    def __init__(self, monitor: RAGMonitor, natural_language_query: str, metadata: Dict[str, Any]):
        self.monitor = monitor
        self.natural_language_query = natural_language_query
        self.metadata = metadata
        self.start_time = None
        self.query_id = f"query_{int(time.time() * 1000)}"
        self.processing_stages = {}
        self.stage_start_times = {}
        self.confidence = 0.0
        self.sql_generated = None
        self.recovery_attempted = False
        self.vector_operations = []
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        total_duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        metrics = QueryMetrics(
            query_id=self.query_id,
            natural_language_query=self.natural_language_query,
            timestamp=datetime.now(),
            processing_stages=self.processing_stages,
            total_duration_ms=total_duration_ms,
            success=success,
            confidence=self.confidence,
            sql_generated=self.sql_generated,
            error_message=error_message,
            recovery_attempted=self.recovery_attempted,
            vector_operations=self.vector_operations
        )
        
        self.monitor.record_query_metrics(metrics)
    
    def start_stage(self, stage_name: str):
        """Start timing a processing stage"""
        self.stage_start_times[stage_name] = time.time()
    
    def end_stage(self, stage_name: str):
        """End timing a processing stage"""
        if stage_name in self.stage_start_times:
            duration_ms = (time.time() - self.stage_start_times[stage_name]) * 1000
            self.processing_stages[stage_name] = duration_ms
            del self.stage_start_times[stage_name]
    
    def set_confidence(self, confidence: float):
        """Set query confidence score"""
        self.confidence = confidence
    
    def set_sql_generated(self, sql: str):
        """Set generated SQL"""
        self.sql_generated = sql
    
    def set_recovery_attempted(self, attempted: bool):
        """Set whether recovery was attempted"""
        self.recovery_attempted = attempted
    
    def add_vector_operation(self, operation: VectorOperation):
        """Add a vector operation to this query"""
        self.vector_operations.append(operation)


# Global monitor instance
_monitor = None

def get_rag_monitor() -> RAGMonitor:
    """Get global RAG monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = RAGMonitor()
    return _monitor

def setup_monitoring(monitoring_dir: str = "monitoring", 
                    alert_thresholds: Dict[str, Any] = None) -> RAGMonitor:
    """Setup RAG monitoring system"""
    global _monitor
    _monitor = RAGMonitor(monitoring_dir, alert_thresholds=alert_thresholds)
    return _monitor


# Example usage and testing
if __name__ == "__main__":
    # Setup monitoring
    monitor = setup_monitoring()
    
    # Add a simple alert callback
    def alert_callback(alert: PerformanceAlert):
        print(f"ALERT: {alert.severity.upper()} - {alert.message}")
    
    monitor.add_alert_callback(alert_callback)
    
    # Simulate some operations
    print("Simulating vector operations...")
    
    for i in range(10):
        with monitor.track_vector_operation('store', vector_count=5) as tracker:
            time.sleep(0.01)  # Simulate work
            if i == 7:  # Simulate an error
                raise Exception("Simulated error")
    
    print("Simulating query processing...")
    
    for i in range(5):
        with monitor.track_query_processing(f"Test query {i}") as tracker:
            tracker.start_stage('intent_analysis')
            time.sleep(0.02)
            tracker.end_stage('intent_analysis')
            
            tracker.start_stage('sql_generation')
            time.sleep(0.03)
            tracker.end_stage('sql_generation')
            
            tracker.set_confidence(0.8 + i * 0.05)
            tracker.set_sql_generated(f"SELECT * FROM table{i}")
    
    # Record system metrics
    monitor.record_system_metrics()
    
    # Get performance summary
    summary = monitor.get_performance_summary(hours=1)
    print(f"\nPerformance Summary:")
    print(json.dumps(summary, indent=2))
    
    # Export metrics
    monitor.export_metrics("test_metrics.json")
    print("\nMetrics exported to test_metrics.json")