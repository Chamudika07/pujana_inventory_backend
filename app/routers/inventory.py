from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import inventory as inventory_model
from app import  oauth2
from app.database import get_db
from app.schemas import inventory
from sqlalchemy import func
from typing import List


router = APIRouter(
    prefix="/inventory",
    tags=['inventory']
)


