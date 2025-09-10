import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    queue_name: str


@dataclass
class MongoConfig:
    uri: str
    database: str
    collection: str


@dataclass
class ScrapingConfig:
    timeout: int
    max_retries: int
    delay_between_requests: float


@dataclass
class Settings:
    redis: RedisConfig
    mongo: MongoConfig
    scraping: ScrapingConfig

    @classmethod
    def load_from_env(cls):
        # Build MongoDB URI if not set
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            mongo_user = os.getenv("MONGO_USERNAME")
            mongo_pass = os.getenv("MONGO_PASSWORD")
            mongo_host = os.getenv("MONGO_HOST", "localhost")
            mongo_port = os.getenv("MONGO_PORT", 27017)
            mongo_db = os.getenv("MONGO_DATABASE")
            mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"

        return cls(
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                queue_name=os.getenv("REDIS_QUEUE_NAME", "articles_queue"),
            ),
            mongo=MongoConfig(
                uri=mongo_uri,
                database=os.getenv("MONGO_DATABASE", "articles_db"),
                collection=os.getenv("MONGO_COLLECTION", "articles"),
            ),
            scraping=ScrapingConfig(
                timeout=int(os.getenv("SCRAPER_TIMEOUT", 30)),
                max_retries=int(os.getenv("SCRAPER_MAX_RETRIES", 3)),
                delay_between_requests=float(os.getenv("SCRAPER_DELAY", 1.0)),
            ),
        )


# Load settings once
settings = Settings.load_from_env()
