from sqlmodel import Session
from sqlalchemy import text

def get_database_size(session: Session) -> str:
    size = session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
    return size