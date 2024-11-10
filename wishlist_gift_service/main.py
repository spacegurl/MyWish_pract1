from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
import requests
import uvicorn

DATABASE_URL = "postgresql://wishlist:password@wishlist-db:5432/wishlist_db"
USER_SERVICE_URL = "http://user-service:8001"

app = FastAPI()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Wishlist(Base):
    __tablename__ = "wishlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    gifts = relationship("Gift", back_populates="wishlist")

class Gift(Base):
    __tablename__ = "gifts"
    id = Column(Integer, primary_key=True, index=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id"))
    name = Column(String)
    wishlist = relationship("Wishlist", back_populates="gifts")

Base.metadata.create_all(bind=engine)

# Pydantic models
class WishlistCreate(BaseModel):
    user_id: int

class GiftCreate(BaseModel):
    wishlist_id: int
    name: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create wishlist endpoint
@app.post("/wishlists/")
def create_wishlist(wishlist: WishlistCreate, db: SessionLocal = Depends(get_db)):
    response = requests.get(f"{USER_SERVICE_URL}/users/{wishlist.user_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="User does not exist")
    new_wishlist = Wishlist(user_id=wishlist.user_id)
    db.add(new_wishlist)
    db.commit()
    db.refresh(new_wishlist)
    return new_wishlist

# Add gift to wishlist
@app.post("/gifts/")
def add_gift(gift: GiftCreate, db: SessionLocal = Depends(get_db)):
    db_wishlist = db.query(Wishlist).filter(Wishlist.id == gift.wishlist_id).first()
    if not db_wishlist:
        raise HTTPException(status_code=400, detail="Wishlist not found")
    new_gift = Gift(wishlist_id=gift.wishlist_id, name=gift.name)
    db.add(new_gift)
    db.commit()
    db.refresh(new_gift)
    return new_gift

# Remove gift from wishlist
@app.delete("/gifts/{gift_id}")
def remove_gift(gift_id: int, db: SessionLocal = Depends(get_db)):
    db.query(Gift).filter(Gift.id == gift_id).delete()
    db.commit()
    return {"message": f"Gift {gift_id} removed from wishlist"}

# Make wishlist public/private
@app.put("/wishlists/{wishlist_id}/visibility")
def set_visibility(wishlist_id: int, is_public: bool, db: SessionLocal = Depends(get_db)):
    db_wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not db_wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    # Set the wishlist as public/private (simulated)
    return {"message": f"Wishlist {wishlist_id} visibility set to {'public' if is_public else 'private'}"}

# Get wishlist details
@app.get("/wishlists/{wishlist_id}")
def get_wishlist(wishlist_id: int, db: SessionLocal = Depends(get_db)):
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return wishlist

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
