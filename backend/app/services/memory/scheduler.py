"""
Scheduler for Memory Evolution Agent
HEARTBEAT.md integration for background runs
"""

import os
import sys
import time
import json
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import threading

from evolution_agent import EvolutionAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    """
    Scheduler that runs evolution cycles on a heartbeat pattern.
    Designed to integrate with HEARTBEAT.md specifications.
    """
    
    def __init__(
        self,
        agent: EvolutionAgent,
        interval_minutes: float = 60.0,  # Default: hourly
        heartbeat_file: str = "heartbeat.json",
        state_file: str = "scheduler_state.json"
    ):
        self.agent = agent
        self.interval = interval_minutes * 60  # Convert to seconds
        self.heartbeat_file = heartbeat_file
        self.state_file = state_file
        
        self._running = False
        self._last_run: Optional[float] = None
        self._run_count = 0
        self._lock = threading.Lock()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self._load_state()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def _load_state(self):
        """Load scheduler state from disk"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self._last_run = state.get('last_run')
                    self._run_count = state.get('run_count', 0)
                    logger.info(f"Loaded state: last_run={self._last_run}, runs={self._run_count}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Persist scheduler state to disk"""
        state = {
            'last_run': self._last_run,
            'run_count': self._run_count,
            'interval_minutes': self.interval / 60,
            'updated_at': time.time()
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save state: {e}")
    
    def _write_heartbeat(self, status: str = "running", details: Optional[Dict] = None):
        """Write heartbeat file for external monitoring"""
        heartbeat = {
            'timestamp': time.time(),
            'datetime': datetime.utcnow().isoformat(),
            'status': status,
            'run_count': self._run_count,
            'next_run': self._last_run + self.interval if self._last_run else time.time() + self.interval,
            'agent_stats': self.agent.get_stats() if self.agent else None,
            'details': details or {}
        }
        
        try:
            with open(self.heartbeat_file, 'w') as f:
                json.dump(heartbeat, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to write heartbeat: {e}")
    
    def run_cycle(self) -> Dict:
        """Execute one evolution cycle"""
        logger.info(f"Starting evolution cycle #{self._run_count + 1}")
        
        start_time = time.time()
        
        try:
            # Run the evolution
            results = self.agent.run_evolution_cycle()
            
            # Get stats
            stats = self.agent.get_stats()
            
            duration = time.time() - start_time
            
            cycle_result = {
                'success': True,
                'cycle_number': self._run_count + 1,
                'duration_seconds': duration,
                'results': results,
                'stats': stats,
                'timestamp': time.time()
            }
            
            logger.info(
                f"Cycle complete: processed={results['memories_processed']}, "
                f"inferred={results['relationships_inferred']}, "
                f"rewrites={results['rewrites_applied']}, "
                f"took={duration:.2f}s"
            )
            
            return cycle_result
            
        except Exception as e:
            logger.exception("Evolution cycle failed")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def start(self):
        """Start the scheduler loop"""
        logger.info(f"Starting scheduler with interval={self.interval/60:.1f} minutes")
        self._running = True
        
        # Write initial heartbeat
        self._write_heartbeat(status="starting")
        
        while self._running:
            current_time = time.time()
            
            # Check if it's time to run
            should_run = (
                self._last_run is None or 
                (current_time - self._last_run) >= self.interval
            )
            
            if should_run:
                # Write heartbeat before run
                self._write_heartbeat(status="running", details={'action': 'evolution_cycle'})
                
                # Run the cycle
                result = self.run_cycle()
                
                # Update state
                with self._lock:
                    self._last_run = current_time
                    self._run_count += 1
                
                self._save_state()
                
                # Write heartbeat after run
                self._write_heartbeat(
                    status="waiting", 
                    details={'last_cycle': result}
                )
            
            # Sleep in small increments to allow for responsive shutdown
            for _ in range(int(self.interval / 10)):
                if not self._running:
                    break
                time.sleep(min(10, self.interval / 10))
        
        logger.info("Scheduler stopped")
        self._write_heartbeat(status="stopped")
    
    def start_once(self) -> Dict:
        """Run one cycle and exit (for cron/job scheduling)"""
        logger.info("Running single evolution cycle")
        
        self._write_heartbeat(status="running_once")
        result = self.run_cycle()
        
        with self._lock:
            self._last_run = time.time()
            self._run_count += 1
        
        self._save_state()
        self._write_heartbeat(status="complete", details={'result': result})
        
        return result
    
    def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("Stopping scheduler...")
        self._running = False
        self._write_heartbeat(status="stopping")
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        current_time = time.time()
        
        return {
            'running': self._running,
            'last_run': self._last_run,
            'next_run': self._last_run + self.interval if self._last_run else None,
            'run_count': self._run_count,
            'interval_minutes': self.interval / 60,
            'time_until_next_run': (
                (self._last_run + self.interval - current_time) 
                if self._last_run else 0
            ),
            'agent_stats': self.agent.get_stats() if self.agent else None
        }


def create_daemon_scheduler(
    storage_path: str = "memory_store.json",
    interval_minutes: float = 60.0,
    heartbeat_file: str = "heartbeat.json",
    log_file: Optional[str] = None
) -> HeartbeatScheduler:
    """
    Create a configured scheduler instance.
    
    Args:
        storage_path: Path to memory storage file
        interval_minutes: Minutes between evolution cycles
        heartbeat_file: Path to heartbeat status file
        log_file: Optional file for logging
    """
    # Setup file logging if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
    
    # Create agent
    agent = EvolutionAgent(
        storage_path=storage_path,
        half_life_days=30.0,
        similarity_threshold=0.6
    )
    
    # Create scheduler
    scheduler = HeartbeatScheduler(
        agent=agent,
        interval_minutes=interval_minutes,
        heartbeat_file=heartbeat_file
    )
    
    return scheduler


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Memory Evolution Agent Scheduler"
    )
    parser.add_argument(
        "--storage", "-s",
        default="memory_store.json",
        help="Path to memory storage file"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=60.0,
        help="Minutes between evolution cycles (default: 60)"
    )
    parser.add_argument(
        "--heartbeat", "-b",
        default="heartbeat.json",
        help="Path to heartbeat file"
    )
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="Run once and exit (for cron scheduling)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status and exit"
    )
    parser.add_argument(
        "--log", "-l",
        help="Log to file"
    )
    
    args = parser.parse_args()
    
    # Create scheduler
    scheduler = create_daemon_scheduler(
        storage_path=args.storage,
        interval_minutes=args.interval,
        heartbeat_file=args.heartbeat,
        log_file=args.log
    )
    
    if args.status:
        import pprint
        pprint.pprint(scheduler.get_status())
        sys.exit(0)
    
    if args.once:
        result = scheduler.start_once()
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get('success') else 1)
    
    # Run continuously
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
