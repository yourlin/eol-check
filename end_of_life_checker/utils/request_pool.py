"""
Request pool for parallel API requests.
"""

import concurrent.futures
import multiprocessing
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class RequestPool:
    """Pool for parallel API requests."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize the request pool.
        
        Args:
            max_workers: Maximum number of worker threads. Defaults to CPU count * 2.
        """
        if max_workers is None:
            # Default to CPU count * 2
            max_workers = os.cpu_count() * 2 if os.cpu_count() else 4
        
        self.max_workers = max_workers
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
    
    def map(self, func: Callable[[Any], T], items: List[Any]) -> List[T]:
        """Execute a function for each item in parallel.
        
        Args:
            func: Function to execute
            items: List of items to process
            
        Returns:
            List of results
        """
        # Submit all tasks
        futures = [self._executor.submit(func, item) for item in items]
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Log the error but continue with other requests
                print(f"Error in request pool: {e}")
        
        return results
    
    def submit(self, func: Callable[[Any], T], *args, **kwargs) -> concurrent.futures.Future:
        """Submit a task to the pool.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Future object
        """
        future = self._executor.submit(func, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def wait_for_completion(self):
        """Wait for all submitted tasks to complete."""
        concurrent.futures.wait(self._futures)
    
    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
