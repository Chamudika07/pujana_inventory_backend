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

#login user
@router.post("/login", response_model=token.Token)
def login_user(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    user = db.query(user_model.User).filter(user_model.User.email == user_credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid Credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid password Credentials")
    
    # create a token
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}