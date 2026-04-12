from dataclasses import dataclass
from typing import Optional

@dataclass
class GameItem:
    item_id:str
    item_base_id:str
    name:str
    category:str = 'Misc'
    description:str = ""
    quantity:int = 1
    stackable:bool = True
    icon_path: Optional[str] = None
    rarity:str = "Common"
    value:int = 0

    attack:int = 0
    defense:int = 0
    heal:int = 0
    equip_slot: Optional[str] = None

    def add(self, amount:int=1) -> None:
        self.quantity = max(0, self.quantity + amount)