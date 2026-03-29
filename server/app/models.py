from pydantic import BaseModel


class ShopProfile(BaseModel):
    id: str
    name: str
    sections: list[str]


class ShoppingItem(BaseModel):
    name: str
    checked: bool = False


class CategorizedSection(BaseModel):
    name: str
    items: list[ShoppingItem]


class CategorizedList(BaseModel):
    list_name: str
    shop: str
    sections: list[CategorizedSection]


class CreateShopRequest(BaseModel):
    name: str


class UpdateShopRequest(BaseModel):
    name: str
    sections: list[str]
