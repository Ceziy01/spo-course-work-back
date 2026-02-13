from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

class UserRepository:
    def get_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()
    
    def get_by_id(self, db: Session, id: int):
        return db.query(User).filter(User.id == id).first()
    
    def create(self, db: Session, user_data:UserCreate):
        hashed_password = get_password_hash(user_data.password)
        db_user = User (
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(self, db: Session, user_id: int, **kwargs):
        user = self.get_by_id(db, user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user

user_repository = UserRepository()