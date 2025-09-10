import json
from typing import List
from config.settings import Settings
from core.redis_handler import RedisHandler
from models.article import ArticleTask
from utils.logger import logger


class Publisher:
    def __init__(self, settings: Settings):
        self.redis_handler = RedisHandler(settings.redis)

    def publish_from_file(self, json_file_path: str) -> int:
        """Read JSON file and publish all articles to Redis queue"""
        try:
            articles_data = self._load_json_file(json_file_path)
            if not articles_data:
                return 0

            tasks = self._convert_to_tasks(articles_data)
            published_count = 0

            for task in tasks:
                if self.redis_handler.push_task(task):
                    published_count += 1

            logger.info(f"Published {published_count}/{len(tasks)} tasks to Redis")
            return published_count

        except Exception as e:
            logger.error(f"Failed to publish from file {json_file_path}: {e}")
            return 0

    def _load_json_file(self, file_path: str) -> List[dict]:
        """Load and parse JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} articles from {file_path}")
                return data
            else:
                logger.error(f"Expected JSON array, got {type(data)}")
                return []

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def _convert_to_tasks(self, articles_data: List[dict]) -> List[ArticleTask]:
        """Convert raw JSON data to ArticleTask objects"""
        tasks = []
        for i, article_data in enumerate(articles_data):
            try:
                # Ensure required fields exist
                required_fields = ["url", "source", "category"]
                missing_fields = [
                    field for field in required_fields if field not in article_data
                ]

                if missing_fields:
                    logger.warning(
                        f"Article {i} missing required fields {missing_fields}, skipping"
                    )
                    continue

                task = ArticleTask(
                    id=article_data.get("id", f"article_{i + 1}"),
                    url=article_data["url"],
                    source=article_data["source"],
                    category=article_data["category"],
                    priority=article_data.get("priority", "medium"),
                )
                tasks.append(task)

            except Exception as e:
                logger.error(f"Failed to convert article {i} to task: {e}")
                continue

        return tasks

    def get_queue_status(self) -> dict:
        """Get current queue statistics"""
        queue_length = self.redis_handler.get_queue_length()
        return {
            "queue_length": queue_length,
            "status": "active" if queue_length > 0 else "empty",
        }
