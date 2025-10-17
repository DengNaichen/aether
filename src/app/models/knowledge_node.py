# from pydantic import BaseModel
from sqlalchemy import Column, String, ForeignKey

from src.app.models.base import Base


class KnowledgeNode(Base):
    """
    SQLAlchemy model for KnowledgeNode.
    """
    __tablename__ = "knowledge_node"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    course_id = Column(String, ForeignKey("course.id"))
    description = Column(String, nullable=False)
