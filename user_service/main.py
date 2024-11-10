from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
import uvicorn

DATABASE_URL = "postgresql://user:password@user-db:5432/user_db"

app = FastAPI()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    interests = relationship("Interest", back_populates="user")

class Friend(Base):
    __tablename__ = "friends"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer)

class Interest(Base):
    __tablename__ = "interests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interest = Column(String)
    user = relationship("User", back_populates="interests")

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class InterestCreate(BaseModel):
    user_id: int
    interest: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User registration endpoint
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# User login endpoint
@app.post("/login")
def login_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username, User.password == user.password).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": db_user.id}

# Endpoint to add a friend
@app.post("/friends/add/{friend_id}")
def add_friend(user_id: int, friend_id: int, db: SessionLocal = Depends(get_db)):
    db_friend = Friend(user_id=user_id, friend_id=friend_id)
    db.add(db_friend)
    db.commit()
    return {"message": f"User {friend_id} added as a friend"}

# Endpoint to remove a friend
@app.delete("/friends/remove/{friend_id}")
def remove_friend(user_id: int, friend_id: int, db: SessionLocal = Depends(get_db)):
    db.query(Friend).filter(Friend.user_id == user_id, Friend.friend_id == friend_id).delete()
    db.commit()
    return {"message": f"User {friend_id} removed as a friend"}

# Endpoint to add interests
@app.post("/interests/")
def add_interest(interest: InterestCreate, db: SessionLocal = Depends(get_db)):
    db_interest = Interest(user_id=interest.user_id, interest=interest.interest)
    db.add(db_interest)
    db.commit()
    return {"message": f"Interest '{interest.interest}' added for user {interest.user_id}"}

# Endpoint to edit interests
@app.put("/interests/{interest_id}")
def edit_interest(interest_id: int, new_interest: str, db: SessionLocal = Depends(get_db)):
    db_interest = db.query(Interest).filter(Interest.id == interest_id).first()
    if not db_interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    db_interest.interest = new_interest
    db.commit()
    return {"message": f"Interest {interest_id} updated to '{new_interest}'"}

# Endpoint to share wishlist link
@app.post("/share_wishlist/{wishlist_id}")
def share_wishlist(user_id: int, wishlist_id: int):
    # Simulate sharing the wishlist link (could be more complex in a real scenario)
    return {"message": f"Wishlist {wishlist_id} shared by user {user_id}"}

# Add this to `user_service/main.py`
@app.get("/users/{user_id}")
def get_user(user_id: int, db: SessionLocal = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": db_user.id, "username": db_user.username}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
