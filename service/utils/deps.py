from sqlmodel import Session, create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL est absente de l'environnement")

engine = create_engine(DATABASE_URL)

def get_session():
    return Session(engine)