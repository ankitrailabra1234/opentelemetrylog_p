# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Item
from .schema import ItemCreate



async def create_item(db: AsyncSession, item_in: ItemCreate) -> Item:
    item = Item(
        name=item_in.name,
        description=item_in.description,
        price=item_in.price
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

