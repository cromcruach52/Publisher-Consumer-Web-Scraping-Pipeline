from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class ArticleTask:
    """Represents a task to be processed"""
    id: str
    url: str
    source: str
    category: str
    priority: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArticleTask':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class ScrapedContent:
    """Represents scraped content from a URL"""
    title: str
    content: str
    scraped_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['scraped_at'] = self.scraped_at.isoformat()
        return data

@dataclass
class Article:
    """Complete article with task info and scraped content"""
    id: str
    url: str
    source: str
    category: str
    priority: str
    title: Optional[str] = None
    content: Optional[str] = None
    status: str = "pending"  # pending, completed, failed
    error_message: Optional[str] = None
    created_at: datetime = None
    scraped_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.scraped_at:
            data['scraped_at'] = self.scraped_at.isoformat()
        return data
    
    @classmethod
    def from_task_and_content(cls, task: ArticleTask, content: ScrapedContent) -> 'Article':
        """Create completed article from task and scraped content"""
        return cls(
            id=task.id,
            url=task.url,
            source=task.source,
            category=task.category,
            priority=task.priority,
            title=content.title,
            content=content.content,
            status="completed",
            scraped_at=content.scraped_at
        )
    
    @classmethod
    def from_task_with_error(cls, task: ArticleTask, error_message: str) -> 'Article':
        """Create failed article from task with error"""
        return cls(
            id=task.id,
            url=task.url,
            source=task.source,
            category=task.category,
            priority=task.priority,
            status="failed",
            error_message=error_message
        )
