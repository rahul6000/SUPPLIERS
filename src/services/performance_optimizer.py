"""
Performance optimization system for the Suppliers AI platform.
Handles caching, async processing, database optimization, and monitoring.
"""
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import functools
import gc
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

class CacheManager:
    """Advanced caching system with TTL and memory management"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            if key not in self._cache:
                return None
                
            # Check TTL
            if self._is_expired(key):
                self._remove(key)
                return None
            
            # Update access count
            self._access_count[key] = self._access_count.get(key, 0) + 1
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache with TTL"""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            self._cache[key] = value
            self._timestamps[key] = {
                'created': time.time(),
                'ttl': ttl or self.default_ttl
            }
            self._access_count[key] = 1
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_count.clear()
            gc.collect()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': self._calculate_hit_rate(),
                'memory_usage': self._estimate_memory_usage()
            }
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        
        timestamp_data = self._timestamps[key]
        return time.time() - timestamp_data['created'] > timestamp_data['ttl']
    
    def _remove(self, key: str) -> None:
        """Remove entry from all cache structures"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_count.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self._cache:
            return
        
        # Find least accessed item
        lru_key = min(self._access_count.items(), key=lambda x: x[1])[0]
        self._remove(lru_key)
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                with self._lock:
                    expired_keys = [
                        key for key in self._cache.keys()
                        if self._is_expired(key)
                    ]
                    for key in expired_keys:
                        self._remove(key)
                    
                    if expired_keys:
                        gc.collect()
            except Exception as e:
                logging.error(f"Cache cleanup error: {e}")
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        return 85.5  # Mock implementation
    
    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage (simplified)"""
        return f"{len(self._cache) * 0.5:.1f} KB"


class AsyncProcessor:
    """Asynchronous processing system for heavy operations"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}
        self._task_id_counter = 0
        
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit async task and return task ID"""
        task_id = f"task_{self._task_id_counter}"
        self._task_id_counter += 1
        
        future = self.executor.submit(func, *args, **kwargs)
        self.active_tasks[task_id] = {
            'future': future,
            'submitted_at': datetime.now(),
            'status': 'running'
        }
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of async task"""
        if task_id not in self.active_tasks:
            return {'status': 'not_found'}
        
        task = self.active_tasks[task_id]
        future = task['future']
        
        if future.done():
            try:
                result = future.result()
                task['status'] = 'completed'
                task['result'] = result
                return {
                    'status': 'completed',
                    'result': result,
                    'duration': (datetime.now() - task['submitted_at']).total_seconds()
                }
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                return {
                    'status': 'failed',
                    'error': str(e)
                }
        else:
            return {
                'status': 'running',
                'duration': (datetime.now() - task['submitted_at']).total_seconds()
            }
    
    def wait_for_task(self, task_id: str, timeout: Optional[int] = None) -> Any:
        """Wait for task completion and return result"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        future = self.active_tasks[task_id]['future']
        return future.result(timeout=timeout)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel running task"""
        if task_id not in self.active_tasks:
            return False
        
        future = self.active_tasks[task_id]['future']
        return future.cancel()
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get all active tasks"""
        return {
            task_id: {
                'status': task['status'],
                'duration': (datetime.now() - task['submitted_at']).total_seconds()
            }
            for task_id, task in self.active_tasks.items()
            if task['status'] == 'running'
        }


class DatabaseOptimizer:
    """Database query optimization and connection management"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.query_cache = CacheManager(max_size=500, default_ttl=1800)  # 30 min cache
        self.connection_pool_size = 5
        
    def optimized_query(self, table: str, select: str = "*", filters: Dict[str, Any] = None, cache_key: Optional[str] = None) -> Any:
        """Execute optimized database query with caching"""
        
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = f"{table}_{select}_{str(filters)}"
        
        # Check cache first
        cached_result = self.query_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # Build query
            query = self.supabase.table(table).select(select)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(field, value)
                    else:
                        query = query.eq(field, value)
            
            # Execute query
            result = query.execute()
            
            # Cache result
            self.query_cache.set(cache_key, result, ttl=1800)  # 30 minutes
            
            return result
            
        except Exception as e:
            st.error(f"Database query error: {e}")
            return None
    
    def batch_insert(self, table: str, data: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """Optimized batch insert with chunking"""
        try:
            # Split data into batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                result = self.supabase.table(table).insert(batch).execute()
                
                if hasattr(result, 'error') and result.error:
                    st.error(f"Batch insert error: {result.error}")
                    return False
            
            # Clear related caches
            self._clear_table_cache(table)
            return True
            
        except Exception as e:
            st.error(f"Batch insert error: {e}")
            return False
    
    def batch_update(self, table: str, updates: List[Dict[str, Any]], batch_size: int = 50) -> bool:
        """Optimized batch update"""
        try:
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                for update in batch:
                    if 'id' not in update:
                        continue
                    
                    update_data = {k: v for k, v in update.items() if k != 'id'}
                    result = self.supabase.table(table).update(update_data).eq('id', update['id']).execute()
                    
                    if hasattr(result, 'error') and result.error:
                        st.error(f"Batch update error: {result.error}")
                        return False
            
            self._clear_table_cache(table)
            return True
            
        except Exception as e:
            st.error(f"Batch update error: {e}")
            return False
    
    def _clear_table_cache(self, table: str) -> None:
        """Clear cache entries for specific table"""
        # Simplified - in production, would have more sophisticated cache invalidation
        keys_to_remove = [
            key for key in self.query_cache._cache.keys()
            if key.startswith(table)
        ]
        for key in keys_to_remove:
            self.query_cache.delete(key)


class PerformanceMonitor:
    """Performance monitoring and alerting system"""
    
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            'response_time': 5.0,  # seconds
            'memory_usage': 500,   # MB
            'cache_hit_rate': 80,  # percentage
            'error_rate': 5        # percentage
        }
        self.start_time = time.time()
        
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{time.time()}"
        self.metrics[timer_id] = {'start_time': time.time(), 'operation': operation}
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing and return duration"""
        if timer_id not in self.metrics:
            return 0.0
        
        duration = time.time() - self.metrics[timer_id]['start_time']
        operation = self.metrics[timer_id]['operation']
        
        # Log performance
        self._log_performance(operation, duration)
        
        # Clean up
        del self.metrics[timer_id]
        
        return duration
    
    def log_error(self, error_type: str, message: str) -> None:
        """Log error for monitoring"""
        timestamp = datetime.now().isoformat()
        error_key = f"error_{timestamp}"
        
        self.metrics[error_key] = {
            'type': error_type,
            'message': message,
            'timestamp': timestamp
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'total_operations': len([k for k in self.metrics.keys() if 'operation_' in k]),
            'error_count': len([k for k in self.metrics.keys() if 'error_' in k]),
            'memory_usage_estimated': '125.3 MB',  # Mock
            'cache_efficiency': '87.2%',  # Mock
            'avg_response_time': '1.8s'   # Mock
        }
    
    def _log_performance(self, operation: str, duration: float) -> None:
        """Log performance metrics"""
        perf_key = f"operation_{operation}_{datetime.now().isoformat()}"
        self.metrics[perf_key] = {
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        # Alert if threshold exceeded
        if duration > self.thresholds['response_time']:
            st.warning(f"⚠️ Slow operation detected: {operation} took {duration:.2f}s")


# Decorators for performance optimization
def cached(ttl: int = 3600, cache_manager: Optional[CacheManager] = None):
    """Decorator to cache function results"""
    if cache_manager is None:
        cache_manager = CacheManager()
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            
            # Try cache first
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def timed(monitor: Optional[PerformanceMonitor] = None):
    """Decorator to time function execution"""
    if monitor is None:
        monitor = PerformanceMonitor()
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer_id = monitor.start_timer(func.__name__)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_timer(timer_id)
        return wrapper
    return decorator


class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self, supabase_client=None):
        self.cache_manager = CacheManager(max_size=2000, default_ttl=3600)
        self.async_processor = AsyncProcessor(max_workers=6)
        self.db_optimizer = DatabaseOptimizer(supabase_client)
        self.monitor = PerformanceMonitor()
        
    def optimize_search(self, search_params: Dict[str, Any]) -> Any:
        """Optimized search with caching and async processing"""
        cache_key = f"search_{str(search_params)}"
        
        # Check cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute optimized query
        timer_id = self.monitor.start_timer("search_operation")
        
        try:
            result = self.db_optimizer.optimized_query(
                table="products",
                select="*",
                filters=search_params,
                cache_key=cache_key
            )
            
            self.monitor.end_timer(timer_id)
            return result
            
        except Exception as e:
            self.monitor.end_timer(timer_id)
            self.monitor.log_error("search_error", str(e))
            raise
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        return {
            'cache_stats': self.cache_manager.stats(),
            'active_tasks': self.async_processor.get_active_tasks(),
            'system_stats': self.monitor.get_system_stats(),
            'recommendations': self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        cache_stats = self.cache_manager.stats()
        if cache_stats['hit_rate'] < 80:
            recommendations.append("Consider increasing cache TTL for better hit rates")
        
        if cache_stats['size'] > cache_stats['max_size'] * 0.9:
            recommendations.append("Cache approaching capacity - consider increasing max_size")
        
        active_tasks = len(self.async_processor.get_active_tasks())
        if active_tasks > self.async_processor.max_workers * 0.8:
            recommendations.append("High async task load - consider increasing worker pool")
        
        return recommendations


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()