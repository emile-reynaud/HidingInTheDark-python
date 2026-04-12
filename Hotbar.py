

from typing import Dict, Optional

from GameItem import GameItem


class Hotbar:
    def __init__(self):
        self.items: Dict[str, Optional[GameItem]] = {
            "main_hand": None,
            "off_hand": None,
            "head": None,
            "chest": None,
            "legs": None,
            "feet": None,
            "ring": None
        }
    
    def add_item(self, item:GameItem):
        if self.items[item.equip_slot] is not None:
            old_item = self.items[item.equip_slot]
            self.items[item.equip_slot] = item

            return old_item
        
        else:
            self.items[item.equip_slot] = item
            return None
        
    def remove_item(self, slot:Optional[str]):
        if slot is not None:
            if self.items[slot] is not None:
                old_item = self.items[slot]
                self.items[slot] = None
                return old_item
            else:
                return None
        else:
            return None
        
    def dict_to_GameItem(self, item_dict:dict) -> GameItem:
        entry = GameItem(
            item_id=item_dict.get("item_id"),
            item_base_id=item_dict.get("item_base_id"),
            name=item_dict.get("name"),
            quantity=item_dict.get("quantity"),
            icon_path=item_dict.get("icon_path"),
            description=item_dict.get("description"),
            category=item_dict.get("category"),
            rarity=item_dict.get("rarity"),
            value=item_dict.get("value"),
            stackable=item_dict.get("stackable"),
            attack=item_dict.get("attack"),
            defense=item_dict.get("defense"),
            heal=item_dict.get("heal"),
            equip_slot=item_dict.get("equip_slot")
        )
        return entry
        
    def get_data(self) -> Dict[str, Optional[Dict[str, any]]]:
        items = {}
        for k, v in self.items.items():
            if v is not None:
                items[k] = {
                    "item_id": v.item_id,
                    "item_base_id": v.item_base_id,
                    "name": v.name,
                    "quantity": v.quantity,
                    "icon_path": v.icon_path,
                    "description": v.description,
                    "category": v.category,
                    "rarity": v.rarity,
                    "value": v.value,
                    "stackable": v.stackable,
                    "attack": v.attack,
                    "defense": v.defense,
                    "heal": v.heal,
                    "equip_slot": v.equip_slot
                }
        return items