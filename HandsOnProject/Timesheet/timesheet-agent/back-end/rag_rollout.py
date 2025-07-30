#!/usr/bin/env python3
"""
RAG Rollout Manager - Gradual rollout and fallback management for RAG system.

This module manages the gradual rollout of the RAG system, providing fallback
mechanisms and monitoring to ensure smooth transition from the traditional system.
"""

import os
import time
import random
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from threading import Lock

# Import configuration
from config import (
    USE_RAG_SYSTEM, RAG_ROLLOUT_PERCENTAGE, RAG_FALLBACK_ENABLED,
    RAG_FALLBACK_ERROR_THRESHOLD, RAG_MIGRATION_MODE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RolloutMode(Enum):
    """RAG system rollout modes"""
    DISABLED = "disabled"
    TESTING = "testing"
    GRADUAL = "gradual"
    FULL = "full"


class FallbackReason(Enum):
    """Reasons for falling back to traditional system"""
    RAG_INITIALIZATION_FAILURE = "rag_initialization_failure"
    HIGH_ERROR_RATE = "high_error_rate"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    VECTOR_STORE_CORRUPTION = "vector_store_corruption"
    MANUAL_OVERRIDE = "manual_override"
    ROLLOUT_PERCENTAGE = "rollout_percentage"


@dataclass
class RolloutMetrics:
    """Metrics for rollout monitoring"""
    total_queries: int
    rag_queries: int
    traditional_queries: int
    rag_success_rate: float
    traditional_success_rate: float
    rag_avg_response_time: float
    traditional_avg_response_time: float
    fallback_count: int
    last_updated: datetime


@dataclass
class FallbackEvent:
    """Fallback event information"""
    timestamp: datetime
    reason: FallbackReason
    query: str
    error_message: Optional[str]
    recovery_attempted: bool
    metadata: Dict[str, Any]


class RAGRolloutManager:
    """
    Manager for gradual RAG system rollout with fallback capabilities.
    
    Handles percentage-based rollout, error monitoring, and automatic
    fallback to the traditional system when issues are detected.
    """
    
    def __init__(self, 
                 rollout_percentage: int = None,
                 fallback_enabled: bool = None,
                 error_threshold: int = None,
                 migration_mode: str = None):
        """
        Initialize rollout manager.
        
        Args:
            rollout_percentage: Percentage of queries to route to RAG (0-100)
            fallback_enabled: Whether fallback is enabled
            error_threshold: Number of consecutive errors before fallback
            migration_mode: Migration mode (disabled, testing, gradual, full)
        """
        # Use provided values or fall back to config
        self.rollout_percentage = rollout_percentage if rollout_percentage is not None else RAG_ROLLOUT_PERCENTAGE
        self.fallback_enabled = fallback_enabled if fallback_enabled is not None else RAG_FALLBACK_ENABLED
        self.error_threshold = error_threshold if error_threshold is not None else RAG_FALLBACK_ERROR_THRESHOLD
        self.migration_mode = RolloutMode(migration_mode or RAG_MIGRATION_MODE)
        
        # State tracking
        self._lock = Lock()
        self.consecutive_errors = 0
        self.fallback_active = False
        self.fallback_until = None
        self.rag_available = True
        
        # Metrics tracking
        self.metrics = RolloutMetrics(
            total_queries=0,
            rag_queries=0,
            traditional_queries=0,
            rag_success_rate=1.0,
            traditional_success_rate=1.0,
            rag_avg_response_time=0.0,
            traditional_avg_response_time=0.0,
            fallback_count=0,
            last_updated=datetime.now()
        )
        
        # Event tracking
        self.fallback_events: List[FallbackEvent] = []
        self.max_events = 1000
        
        # Callbacks
        self.fallback_callbacks: List[Callable[[FallbackEvent], None]] = []
        
        logger.info(f"RAG Rollout Manager initialized - Mode: {self.migration_mode.value}, "
                   f"Rollout: {self.rollout_percentage}%, Fallback: {self.fallback_enabled}")
    
    def should_use_rag(self, query: str = None, user_id: str = None) -> bool:
        """
        Determine whether to use RAG system for this query.
        
        Args:
            query: The natural language query
            user_id: Optional user identifier for consistent routing
            
        Returns:
            True if RAG system should be used, False for traditional system
        """
        with self._lock:
            # Check if RAG is disabled
            if self.migration_mode == RolloutMode.DISABLED:
                return False
            
            # Check if RAG system is available
            if not self.rag_available:
                return False
            
            # Check if fallback is active
            if self.fallback_active:
                # Check if fallback period has expired
                if self.fallback_until and datetime.now() > self.fallback_until:
                    self._clear_fallback()
                else:
                    return False
            
            # Full rollout mode
            if self.migration_mode == RolloutMode.FULL:
                return True
            
            # Testing mode - use RAG for specific test patterns
            if self.migration_mode == RolloutMode.TESTING:
                return self._is_test_query(query)
            
            # Gradual rollout mode - use percentage-based routing
            if self.migration_mode == RolloutMode.GRADUAL:
                return self._should_route_to_rag(query, user_id)
            
            return False
    
    def record_query_result(self, 
                           query: str,
                           used_rag: bool,
                           success: bool,
                           response_time: float,
                           error_message: str = None):
        """
        Record the result of a query for metrics and fallback decisions.
        
        Args:
            query: The natural language query
            used_rag: Whether RAG system was used
            success: Whether the query was successful
            response_time: Query response time in seconds
            error_message: Error message if query failed
        """
        with self._lock:
            self.metrics.total_queries += 1
            
            if used_rag:
                self.metrics.rag_queries += 1
                self._update_rag_metrics(success, response_time)
                
                if not success:
                    self.consecutive_errors += 1
                    self._check_fallback_conditions(query, error_message)
                else:
                    self.consecutive_errors = 0
            else:
                self.metrics.traditional_queries += 1
                self._update_traditional_metrics(success, response_time)
            
            self.metrics.last_updated = datetime.now()
    
    def trigger_fallback(self, 
                        reason: FallbackReason,
                        query: str = None,
                        error_message: str = None,
                        duration_minutes: int = 30):
        """
        Manually trigger fallback to traditional system.
        
        Args:
            reason: Reason for fallback
            query: Query that triggered fallback
            error_message: Associated error message
            duration_minutes: How long to maintain fallback
        """
        with self._lock:
            self.fallback_active = True
            self.fallback_until = datetime.now() + timedelta(minutes=duration_minutes)
            self.metrics.fallback_count += 1
            
            # Record fallback event
            event = FallbackEvent(
                timestamp=datetime.now(),
                reason=reason,
                query=query or "manual_trigger",
                error_message=error_message,
                recovery_attempted=False,
                metadata={
                    'duration_minutes': duration_minutes,
                    'consecutive_errors': self.consecutive_errors
                }
            )
            
            self._record_fallback_event(event)
            
            logger.warning(f"Fallback triggered: {reason.value} - Duration: {duration_minutes} minutes")
    
    def clear_fallback(self):
        """Manually clear fallback state"""
        with self._lock:
            self._clear_fallback()
            logger.info("Fallback manually cleared")
    
    def set_rag_availability(self, available: bool):
        """Set RAG system availability status"""
        with self._lock:
            self.rag_available = available
            if not available:
                self.trigger_fallback(
                    FallbackReason.RAG_INITIALIZATION_FAILURE,
                    error_message="RAG system marked as unavailable"
                )
            logger.info(f"RAG availability set to: {available}")
    
    def update_rollout_percentage(self, percentage: int):
        """Update rollout percentage"""
        if not 0 <= percentage <= 100:
            raise ValueError("Rollout percentage must be between 0 and 100")
        
        with self._lock:
            old_percentage = self.rollout_percentage
            self.rollout_percentage = percentage
            logger.info(f"Rollout percentage updated: {old_percentage}% -> {percentage}%")
    
    def get_metrics(self) -> RolloutMetrics:
        """Get current rollout metrics"""
        with self._lock:
            return self.metrics
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rollout status"""
        with self._lock:
            return {
                'migration_mode': self.migration_mode.value,
                'rollout_percentage': self.rollout_percentage,
                'fallback_enabled': self.fallback_enabled,
                'fallback_active': self.fallback_active,
                'fallback_until': self.fallback_until.isoformat() if self.fallback_until else None,
                'rag_available': self.rag_available,
                'consecutive_errors': self.consecutive_errors,
                'error_threshold': self.error_threshold,
                'metrics': self.metrics,
                'recent_fallback_events': len([e for e in self.fallback_events 
                                             if e.timestamp > datetime.now() - timedelta(hours=24)])
            }
    
    def get_fallback_events(self, hours: int = 24) -> List[FallbackEvent]:
        """Get recent fallback events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [event for event in self.fallback_events if event.timestamp >= cutoff_time]
    
    def add_fallback_callback(self, callback: Callable[[FallbackEvent], None]):
        """Add callback for fallback events"""
        self.fallback_callbacks.append(callback)
    
    def _should_route_to_rag(self, query: str = None, user_id: str = None) -> bool:
        """Determine if query should be routed to RAG based on percentage"""
        if self.rollout_percentage == 0:
            return False
        if self.rollout_percentage == 100:
            return True
        
        # Use consistent routing for same user/query combination
        if user_id:
            # Hash user_id to get consistent routing
            hash_value = hash(user_id) % 100
            return hash_value < self.rollout_percentage
        
        # Random routing if no user_id
        return random.randint(1, 100) <= self.rollout_percentage
    
    def _is_test_query(self, query: str) -> bool:
        """Check if query matches test patterns"""
        if not query:
            return False
        
        # Define test query patterns
        test_patterns = [
            "test",
            "demo",
            "example",
            "how many employees",  # Common test query
            "show me all projects"  # Common test query
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in test_patterns)
    
    def _update_rag_metrics(self, success: bool, response_time: float):
        """Update RAG system metrics"""
        if self.metrics.rag_queries == 1:
            # First query
            self.metrics.rag_success_rate = 1.0 if success else 0.0
            self.metrics.rag_avg_response_time = response_time
        else:
            # Update running averages
            total_rag = self.metrics.rag_queries
            
            # Update success rate
            current_successes = self.metrics.rag_success_rate * (total_rag - 1)
            if success:
                current_successes += 1
            self.metrics.rag_success_rate = current_successes / total_rag
            
            # Update average response time
            total_time = self.metrics.rag_avg_response_time * (total_rag - 1)
            self.metrics.rag_avg_response_time = (total_time + response_time) / total_rag
    
    def _update_traditional_metrics(self, success: bool, response_time: float):
        """Update traditional system metrics"""
        if self.metrics.traditional_queries == 1:
            # First query
            self.metrics.traditional_success_rate = 1.0 if success else 0.0
            self.metrics.traditional_avg_response_time = response_time
        else:
            # Update running averages
            total_traditional = self.metrics.traditional_queries
            
            # Update success rate
            current_successes = self.metrics.traditional_success_rate * (total_traditional - 1)
            if success:
                current_successes += 1
            self.metrics.traditional_success_rate = current_successes / total_traditional
            
            # Update average response time
            total_time = self.metrics.traditional_avg_response_time * (total_traditional - 1)
            self.metrics.traditional_avg_response_time = (total_time + response_time) / total_traditional
    
    def _check_fallback_conditions(self, query: str, error_message: str):
        """Check if fallback conditions are met"""
        if not self.fallback_enabled:
            return
        
        # Check consecutive error threshold
        if self.consecutive_errors >= self.error_threshold:
            self.trigger_fallback(
                FallbackReason.HIGH_ERROR_RATE,
                query=query,
                error_message=error_message,
                duration_minutes=60  # Longer fallback for high error rate
            )
            return
        
        # Check success rate threshold
        if self.metrics.rag_queries >= 10:  # Need minimum sample size
            if self.metrics.rag_success_rate < 0.5:  # Less than 50% success rate
                self.trigger_fallback(
                    FallbackReason.HIGH_ERROR_RATE,
                    query=query,
                    error_message="Low success rate detected",
                    duration_minutes=45
                )
                return
        
        # Check performance degradation
        if (self.metrics.rag_queries >= 5 and self.metrics.traditional_queries >= 5):
            if self.metrics.rag_avg_response_time > self.metrics.traditional_avg_response_time * 3:
                self.trigger_fallback(
                    FallbackReason.PERFORMANCE_DEGRADATION,
                    query=query,
                    error_message="Performance degradation detected",
                    duration_minutes=30
                )
    
    def _clear_fallback(self):
        """Clear fallback state"""
        self.fallback_active = False
        self.fallback_until = None
        self.consecutive_errors = 0
    
    def _record_fallback_event(self, event: FallbackEvent):
        """Record a fallback event"""
        self.fallback_events.append(event)
        
        # Limit event history
        if len(self.fallback_events) > self.max_events:
            self.fallback_events = self.fallback_events[-self.max_events:]
        
        # Call callbacks
        for callback in self.fallback_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Fallback callback failed: {e}")
    
    def export_metrics(self, output_file: str):
        """Export rollout metrics to file"""
        try:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'rollout_status': self.get_status(),
                'fallback_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'reason': event.reason.value,
                        'query': event.query,
                        'error_message': event.error_message,
                        'recovery_attempted': event.recovery_attempted,
                        'metadata': event.metadata
                    }
                    for event in self.fallback_events
                ]
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Rollout metrics exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise


# Global rollout manager instance
_rollout_manager = None

def get_rollout_manager() -> RAGRolloutManager:
    """Get global rollout manager instance"""
    global _rollout_manager
    if _rollout_manager is None:
        _rollout_manager = RAGRolloutManager()
    return _rollout_manager

def setup_rollout_manager(**kwargs) -> RAGRolloutManager:
    """Setup rollout manager with custom configuration"""
    global _rollout_manager
    _rollout_manager = RAGRolloutManager(**kwargs)
    return _rollout_manager


# Context manager for query routing
class QueryRouter:
    """Context manager for handling query routing and result tracking"""
    
    def __init__(self, query: str, user_id: str = None):
        self.query = query
        self.user_id = user_id
        self.rollout_manager = get_rollout_manager()
        self.use_rag = False
        self.start_time = None
    
    def __enter__(self):
        self.use_rag = self.rollout_manager.should_use_rag(self.query, self.user_id)
        self.start_time = time.time()
        return self.use_rag
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        response_time = time.time() - self.start_time
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        self.rollout_manager.record_query_result(
            self.query, self.use_rag, success, response_time, error_message
        )


# Example usage and testing
if __name__ == "__main__":
    # Setup rollout manager
    rollout_manager = setup_rollout_manager(
        rollout_percentage=50,
        migration_mode="gradual"
    )
    
    # Add fallback callback
    def fallback_callback(event: FallbackEvent):
        print(f"FALLBACK: {event.reason.value} - {event.query}")
    
    rollout_manager.add_fallback_callback(fallback_callback)
    
    # Simulate queries
    test_queries = [
        "How many employees are there?",
        "Show me all projects",
        "What is the average salary?",
        "List all departments"
    ]
    
    print("Simulating query routing...")
    
    for i, query in enumerate(test_queries * 5):  # 20 queries total
        with QueryRouter(query, user_id=f"user_{i % 3}") as use_rag:
            print(f"Query: {query[:30]}... -> {'RAG' if use_rag else 'Traditional'}")
            
            # Simulate some failures for RAG system
            if use_rag and i % 7 == 0:  # Every 7th RAG query fails
                raise Exception("Simulated RAG failure")
            
            time.sleep(0.01)  # Simulate processing time
    
    # Show final status
    status = rollout_manager.get_status()
    print(f"\nFinal Status:")
    print(f"Total Queries: {status['metrics'].total_queries}")
    print(f"RAG Queries: {status['metrics'].rag_queries}")
    print(f"Traditional Queries: {status['metrics'].traditional_queries}")
    print(f"RAG Success Rate: {status['metrics'].rag_success_rate:.2%}")
    print(f"Fallback Active: {status['fallback_active']}")
    print(f"Fallback Events: {status['recent_fallback_events']}")
    
    # Export metrics
    rollout_manager.export_metrics("rollout_metrics.json")
    print("\nMetrics exported to rollout_metrics.json")