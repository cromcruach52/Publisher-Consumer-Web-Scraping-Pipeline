from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config.settings import MongoConfig
from models.article import Article
from utils.logger import logger
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

class DBHandler:
    def __init__(self, config: MongoConfig):
        self.config = config
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting MongoDB connection (attempt {attempt + 1}/{max_retries})")
                self.client = MongoClient(
                    config.uri,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
                
                # Test connection with admin command
                self.client.admin.command('ping')
                
                self.db = self.client[config.database]
                self.collection = self.db[config.collection]
                
                # Create index on URL for faster lookups and prevent duplicates
                self.collection.create_index("url", unique=True)
                logger.info(f"✅ Connected to MongoDB: {config.database}.{config.collection}")
                break
                
            except Exception as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to connect to MongoDB after {max_retries} attempts: {e}")
                    raise
                
                # Exponential backoff
                time.sleep(retry_delay)
                retry_delay *= 2
    
    def save_article(self, article: Article) -> bool:
        """Save or update an article"""
        try:
            result = self.collection.replace_one(
                {"url": article.url},  # Find by URL
                article.to_dict(),     # Replace with new data
                upsert=True           # Create if doesn't exist
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new article: {article.id}")
            else:
                logger.info(f"Updated existing article: {article.id}")
            
            return True
        except PyMongoError as e:
            logger.error(f"Failed to save article {article.id}: {e}")
            return False
    
    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Retrieve an article by URL"""
        try:
            doc = self.collection.find_one({"url": url})
            if doc:
                # Remove MongoDB's _id field
                doc.pop('_id', None)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in doc and isinstance(doc['created_at'], str):
                    doc['created_at'] = datetime.fromisoformat(doc['created_at'])
                if 'scraped_at' in doc and isinstance(doc['scraped_at'], str):
                    doc['scraped_at'] = datetime.fromisoformat(doc['scraped_at'])
                
                return Article(**doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get article by URL {url}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            total_count = self.collection.count_documents({})
            completed_count = self.collection.count_documents({"status": "completed"})
            failed_count = self.collection.count_documents({"status": "failed"})
            pending_count = self.collection.count_documents({"status": "pending"})
            
            return {
                "total_articles": total_count,
                "completed": completed_count,
                "failed": failed_count,
                "pending": pending_count
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def get_recent_articles(self, limit: int = 10) -> List[Article]:
        """Get recent articles"""
        try:
            docs = self.collection.find().sort("created_at", -1).limit(limit)
            articles = []
            
            for doc in docs:
                doc.pop('_id', None)
                # Convert datetime strings back to datetime objects
                if 'created_at' in doc and isinstance(doc['created_at'], str):
                    doc['created_at'] = datetime.fromisoformat(doc['created_at'])
                if 'scraped_at' in doc and isinstance(doc['scraped_at'], str):
                    doc['scraped_at'] = datetime.fromisoformat(doc['scraped_at'])
                
                articles.append(Article(**doc))
            
            return articles
        except Exception as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []
