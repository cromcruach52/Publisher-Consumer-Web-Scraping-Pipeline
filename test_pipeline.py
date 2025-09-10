#!/usr/bin/env python3
"""
Simple test runner for the pipeline
"""

import json
import time
from config.settings import Settings
from core.publisher import Publisher
from core.consumer import Consumer
from utils.logger import logger

def run_simple_test():
    """Run a simple end-to-end test"""
    try:
        logger.info("🧪 Starting pipeline test...")
        
        # Load settings
        settings = Settings.load_from_env()
        
        # Test data
        test_articles = [
            {
                "id": "test_1",
                "url": "https://httpbin.org/html",
                "source": "test",
                "category": "test"
            }
        ]
        
        # Save test data
        with open('test_articles.json', 'w') as f:
            json.dump(test_articles, f)
        
        # Test publisher
        logger.info("Testing publisher...")
        publisher = Publisher(settings)
        published = publisher.publish_from_file('test_articles.json')
        
        if published > 0:
            logger.info(f"✅ Published {published} test articles")
            
            # Test consumer (process one item)
            logger.info("Testing consumer...")
            consumer = Consumer(settings)
            
            # Process one task
            task = consumer.redis_handler.pop_task(timeout=10)
            if task:
                success = consumer._process_task(task)
                if success:
                    logger.info("✅ Consumer test successful")
                    
                    # Show stats
                    stats = consumer.get_stats()
                    logger.info(f"Final stats: {stats}")
                    
                    return True
                else:
                    logger.error("❌ Consumer test failed")
            else:
                logger.error("❌ No task found in queue")
        else:
            logger.error("❌ Publisher test failed")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_test()
    exit(0 if success else 1)
