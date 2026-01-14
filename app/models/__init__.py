from app.models.base import Base

# Import ALL models so Alembic can see them
from app.models.user import User
from app.models.category import Category
from app.models.item import Item
from app.models.inventory import InventoryTransaction
