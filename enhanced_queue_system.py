# Simple Bot Queue System - Fixed Version
# Replaces the complex enhanced queue that was causing event loop conflicts

import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

@dataclass
class BotTask:
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 300.0
    retries: int = 3
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class SimpleBotQueue:
    """Simple thread-based queue system that works with aiogram."""
    
    def __init__(self, max_workers: int = 4):
        # Thread-safe queue (no asyncio conflicts)
        self.task_queue = queue.PriorityQueue()
        self.result_cache = {}
        self.task_status = {}
        
        # Thread pool for workers
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(
            max_workers=max_workers, 
            thread_name_prefix="BotWorker"
        )
        
        # Statistics
        self.total_processed = 0
        self.total_errors = 0
        self.worker_stats = {
            i: {'processed': 0, 'errors': 0, 'last_activity': time.time()} 
            for i in range(max_workers)
        }
        
        # Rate limiting
        self.rate_limit_requests = []
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 50     # 50 requests per minute
        
        # Circuit breaker
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 10
        self.circuit_breaker_open = False
        self.circuit_breaker_last_failure = 0
        
        # Start background workers
        self._start_workers()
        
        logging.info(f"SimpleBotQueue initialized with {max_workers} workers")
    
    def _start_workers(self):
        """Start worker threads that monitor the queue."""
        for worker_id in range(self.max_workers):
            worker_thread = threading.Thread(
                target=self._worker_thread, 
                args=(worker_id,), 
                daemon=True,
                name=f"BotWorker-{worker_id}"
            )
            worker_thread.start()
    
    def _worker_thread(self, worker_id: int):
        """Worker thread that processes tasks from queue."""
        logging.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get task from queue with timeout
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check circuit breaker
                if self.circuit_breaker_open:
                    if time.time() - self.circuit_breaker_last_failure > 60:
                        self.circuit_breaker_open = False
                        self.circuit_breaker_failures = 0
                        logging.info("Circuit breaker reset")
                    else:
                        # Put task back and wait
                        self.task_queue.put((priority, task))
                        time.sleep(1)
                        continue
                
                # Process the task
                self._process_task_sync(task, worker_id)
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Update worker stats
                self.worker_stats[worker_id]['processed'] += 1
                self.worker_stats[worker_id]['last_activity'] = time.time()
                
            except Exception as e:
                logging.error(f"Worker {worker_id} thread error: {e}")
                self.worker_stats[worker_id]['errors'] += 1
                time.sleep(1)
    
    def _process_task_sync(self, task: BotTask, worker_id: int):
        """Process a single task synchronously in worker thread."""
        start_time = time.time()
        
        for attempt in range(task.retries + 1):
            try:
                self.task_status[task.task_id] = {
                    'status': 'processing',
                    'worker_id': worker_id,
                    'attempt': attempt + 1,
                    'start_time': start_time
                }
                
                # Execute the function with timeout
                future = self.thread_pool.submit(task.func, *task.args, **task.kwargs)
                result = future.result(timeout=task.timeout)
                
                # Success
                self.result_cache[task.task_id] = {
                    'result': result,
                    'status': 'completed',
                    'completed_at': time.time(),
                    'processing_time': time.time() - start_time,
                    'worker_id': worker_id
                }
                
                self.total_processed += 1
                self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)
                
                logging.debug(f"Task {task.task_id} completed by worker {worker_id}")
                return
                
            except Exception as e:
                logging.error(f"Task {task.task_id} error on attempt {attempt + 1}: {e}")
                
                if attempt == task.retries:
                    # Final failure
                    self.result_cache[task.task_id] = {
                        'error': str(e),
                        'status': 'failed',
                        'completed_at': time.time(),
                        'processing_time': time.time() - start_time,
                        'worker_id': worker_id
                    }
                    self.total_errors += 1
                    self._handle_circuit_breaker()
                else:
                    # Retry with exponential backoff
                    time.sleep(2 ** attempt)
    
    def _handle_circuit_breaker(self):
        """Handle circuit breaker logic."""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            logging.warning(f"Circuit breaker opened after {self.circuit_breaker_failures} failures")
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        
        # Clean old requests
        self.rate_limit_requests = [
            req_time for req_time in self.rate_limit_requests
            if current_time - req_time < self.rate_limit_window
        ]
        
        if len(self.rate_limit_requests) >= self.rate_limit_max:
            return False
        
        self.rate_limit_requests.append(current_time)
        return True
    
    def submit_task(self, 
                   task_id: str,
                   func: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   timeout: float = 300.0,
                   retries: int = 3) -> bool:
        """Submit task to queue."""
        
        if not self._check_rate_limit():
            logging.warning(f"Rate limit exceeded for task {task_id}")
            return False
        
        kwargs = kwargs or {}
        
        task = BotTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            retries=retries
        )
        
        try:
            # Add to priority queue
            self.task_queue.put((priority.value, task))
            
            self.task_status[task_id] = {
                'status': 'queued',
                'queued_at': time.time()
            }
            
            logging.debug(f"Task {task_id} queued with priority {priority.name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to submit task {task_id}: {e}")
            return False
    
    def get_task_result(self, task_id: str, timeout: float = 60.0) -> Any:
        """Get task result with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.result_cache:
                result = self.result_cache.pop(task_id)
                self.task_status.pop(task_id, None)
                
                if result['status'] == 'completed':
                    return result['result']
                else:
                    raise Exception(f"Task failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(0.1)
        
        # Clean up on timeout
        self.task_status.pop(task_id, None)
        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        current_time = time.time()
        
        # Count healthy workers
        healthy_workers = sum(
            1 for stats in self.worker_stats.values()
            if current_time - stats['last_activity'] < 300
        )
        
        return {
            'queue_size': self.task_queue.qsize(),
            'total_processed': self.total_processed,
            'total_errors': self.total_errors,
            'healthy_workers': healthy_workers,
            'total_workers': self.max_workers,
            'active_tasks': len(self.task_status),
            'cached_results': len(self.result_cache),
            'rate_limit_current': len(self.rate_limit_requests),
            'rate_limit_max': self.rate_limit_max,
            'circuit_breaker_open': self.circuit_breaker_open,
            'circuit_breaker_failures': self.circuit_breaker_failures
        }
    
    def health_check(self) -> Dict:
        """Check system health."""
        current_time = time.time()
        
        # Check worker health
        healthy_workers = sum(
            1 for stats in self.worker_stats.values()
            if current_time - stats['last_activity'] < 300
        )
        
        # Check error rate
        total_ops = self.total_processed + self.total_errors
        error_rate = (self.total_errors / total_ops) if total_ops > 0 else 0
        
        # Check queue health
        queue_healthy = self.task_queue.qsize() < 100  # Arbitrary threshold
        
        health_status = {
            'healthy': (
                healthy_workers >= self.max_workers // 2 and
                queue_healthy and
                error_rate < 0.1 and
                not self.circuit_breaker_open
            ),
            'healthy_workers': healthy_workers,
            'total_workers': self.max_workers,
            'queue_healthy': queue_healthy,
            'error_rate': error_rate,
            'circuit_breaker_open': self.circuit_breaker_open,
            'last_check': current_time
        }
        
        return health_status
    
    def shutdown(self):
        """Gracefully shutdown the queue system."""
        logging.info("Shutting down SimpleBotQueue...")
        
        # Wait for current tasks to complete
        self.thread_pool.shutdown(wait=True, timeout=30)
        
        logging.info("SimpleBotQueue shutdown complete")

# Global queue instance
bot_queue = SimpleBotQueue(max_workers=4)



# Simple async wrapper for compatibility with aiogram
async def run_in_executor_simple(func, *args, **kwargs):
    """Simple async wrapper using aiogram's event loop."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(bot_queue.thread_pool, lambda: func(*args, **kwargs))

# Convenience functions for backward compatibility
def submit_task(task_id: str, func: Callable, *args, priority=TaskPriority.NORMAL, **kwargs):
    """Submit task to queue - simplified interface."""
    return bot_queue.submit_task(
        task_id=task_id,
        func=func,
        args=args,
        kwargs=kwargs,
        priority=priority
    )

def get_task_result(task_id: str, timeout: float = 60.0):
    """Get task result - simplified interface."""
    return bot_queue.get_task_result(task_id, timeout)

def get_stats():
    """Get queue statistics - simplified interface."""
    return bot_queue.get_queue_stats()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)