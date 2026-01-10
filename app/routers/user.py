from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import user as user_model
from app import utils , oauth2
from app.database import get_db
from app.schemas import user , token
from fastapi.security.oauth2 import OAuth2PasswordRequestForm


router = APIRouter(
    prefix="/users",
    tags=['Users']
)

# Create User
@router.post("/", response_model=user.UserOut)
def create_user(user: user.UserCreate, db: Session = Depends(get_db)):
    # check if user email already exists
    exiting_user = db.query(user_model.User).filter(user_model.User.email == user.email).first()
    if exiting_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User with email {user.email} already exists")

    #hash the password - user.password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    
    # create user object
    new_user = user_model.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user