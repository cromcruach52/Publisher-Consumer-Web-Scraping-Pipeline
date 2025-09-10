import signal
import sys
from typing import Optional
from config.settings import Settings
from core.redis_handler import RedisHandler
from core.db_handler import DBHandler
from core.scraper import Scraper
from models.article import ArticleTask, Article
from utils.logger import logger


class Consumer:
    def __init__(self, settings: Settings):
        self.redis_handler = RedisHandler(settings.redis)
        self.db_handler = DBHandler(settings.mongo)
        self.scraper = Scraper(settings.scraping)
        self.running = False

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start_consuming(self) -> None:
        """Start the consumer loop"""
        self.running = True
        logger.info("Consumer started. Waiting for tasks...")

        processed_count = 0

        while self.running:
            try:
                task = self.redis_handler.pop_task(timeout=5)
                if task:
                    success = self._process_task(task)
                    if success:
                        processed_count += 1
                        logger.info(f"Total processed: {processed_count}")
                else:
                    # No task available, just continue
                    logger.debug("No tasks in queue, waiting...")

            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}")

        logger.info(f"Consumer stopped. Total processed: {processed_count}")

    def _process_task(self, task: ArticleTask) -> bool:
        """Process a single task"""
        logger.info(f"Processing task: {task.id} - {task.url}")

        try:
            # Always scrape and save, bypassing the "already scraped" check
            scraped_content = self.scraper.scrape(task.url)

            if scraped_content:
                # Create article with scraped content
                article = Article.from_task_and_content(task, scraped_content)

                # Save article (DBHandler will handle upsert automatically)
                success = self.db_handler.save_article(article)

                if success:
                    logger.info(f"Successfully processed task {task.id}")
                    return True
                else:
                    logger.error(f"Failed to save article {task.id} to database")
            else:
                logger.error(f"Failed to scrape content for {task.id}")

            # If we reach here, something failed
            failed_article = Article.from_task_with_error(
                task, "Failed to scrape or save content"
            )
            self.db_handler.save_article(failed_article)
            return False

        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            failed_article = Article.from_task_with_error(task, str(e))
            self.db_handler.save_article(failed_article)
            return False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def get_stats(self) -> dict:
        """Get consumer statistics"""
        db_stats = self.db_handler.get_stats()
        queue_length = self.redis_handler.get_queue_length()

        return {"queue_length": queue_length, "database_stats": db_stats}
