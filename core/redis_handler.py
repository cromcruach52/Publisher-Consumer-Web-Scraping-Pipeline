import redis
import json
from typing import Optional
from config.settings import RedisConfig
from models.article import ArticleTask
from utils.logger import logger

class RedisHandler:
    def __init__(self, config: RedisConfig):
        self.config = config
        self.client = redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            decode_responses=True  # Important: auto-decode bytes to str
        )
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {config.host}:{config.port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
    def push_task(self, task: ArticleTask) -> bool:
        """Push a task to the Redis queue"""
        try:
            serialized_task = json.dumps(task.to_dict())
            self.client.lpush(self.config.queue_name, serialized_task)
            logger.info(f"Pushed task {task.id} to queue")
            return True
        except Exception as e:
            logger.error(f"Failed to push task {task.id}: {e}")
            return False
    
    def pop_task(self, timeout: int = 5) -> Optional[ArticleTask]:
        """Pop a task from Redis queue (blocking)"""
        try:
            result = self.client.brpop(self.config.queue_name, timeout=timeout)
            if result:
                _, serialized_task = result  # brpop returns (queue_name, value)
                task_data = json.loads(serialized_task)
                task = ArticleTask.from_dict(task_data)
                logger.info(f"Popped task {task.id} from queue")
                return task
            return None
        except Exception as e:
            logger.error(f"Failed to pop task: {e}")
            return None
    
    def get_queue_length(self) -> int:
        """Get current queue length"""
        try:
            return self.client.llen(self.config.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0
    
    def clear_queue(self) -> bool:
        """Clear all tasks from queue (useful for testing)"""
        try:
            self.client.delete(self.config.queue_name)
            logger.info("Cleared Redis queue")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False
