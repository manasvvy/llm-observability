from __future__ import annotations

from dotenv import load_dotenv

from app.main import app

load_dotenv()

__all__ = ["app"]
