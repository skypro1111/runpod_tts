from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

engine = create_engine(settings.SQLITE_URL, echo=True)

async def create_db_and_tables() -> None:
    """Create database tables and initial superuser."""
    SQLModel.metadata.create_all(engine)
    
    # Create first superuser if it doesn't exist
    with Session(engine) as session:
        user = session.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        if not user:
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_superuser=True,
            )
            session.add(user)
            session.commit()

def get_session():
    with Session(engine) as session:
        yield session 