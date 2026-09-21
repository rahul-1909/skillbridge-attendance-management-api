"""
Root deployment entrypoint module for SkillBridge Attendance API.
Provides seamless compatibility when cloud platforms deploy from repository root.
"""
from submission.src.main import app

__all__ = ["app"]
