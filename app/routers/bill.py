from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app import  oauth2
from app.database import get_db
from sqlalchemy import func
from typing import Literal
from app.function.automatic_bill_id_generation import generate_bill_id
from app.models.bill import Bill

router = APIRouter(
    prefix = '/bill',
    tags = ['bill']
)

#start bill Api (buy or sell button click)
@router.post("/start")
def start_bill(bill_type : Literal["buy" , "sell"],
               db : Session = Depends(get_db),
               current_user : int = Depends(oauth2.get_current_user)):
    
    bill_id = generate_bill_id(bill_type)
    
    bill = Bill(bill_id = bill_id , bill_type = bill_type)
    
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    return {
        "bill_id" : bill.bill_id ,
        "bull_type" : bill.bill_type ,
        "message" : f"{bill_type.upper()} bill started "
    }
    