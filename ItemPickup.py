import pygame

from config import TILE_SIZE

"""
item_data = {
    "id": "knife",
    "name": "Knife",
    "category": "Weapon",
    "description": "A simple Bowie knife.",
    "quantity": 1,
    "stackable": False,
    "icon_path": "assets/textures/items/iron_sword.png",
    "value": 25,
    "attack": 8,
    "defense": 0,
    "heal": 0,
    "equip_slot": "weapon",   # weapon, helmet, chest, ring...
    "rarity": "common"
}
item_data = {
    "id": "health_potion",
    "name": "Health Potion",
    "category": "Consumable",
    "description": "Restores 30 HP.",
    "quantity": 1,
    "stackable": True,
    "icon_path": "assets/textures/items/health_potion.png",
    "heal": 30,
    "value": 10
}
"""

class ItemPickup(pygame.sprite.Sprite):
    def __init__(self, col, row, item_data, size=30):
        super().__init__()
        self.item_data = item_data
        self.col = col
        self.row = row

        image = pygame.image.load(item_data['icon_path']).convert_alpha()
        self.image = pygame.transform.scale(image, (size, size))
        self.rect = self.image.get_rect()
        
        self.rect.topleft = (
            col * TILE_SIZE + (TILE_SIZE - size) // 2,
            row * TILE_SIZE + (TILE_SIZE - size) // 2
        )
    
    def draw(self, surface, camera, alpha=255):
        img = self.image.copy()
        img.set_alpha(alpha)
        surface.blit(img, (self.rect.x - camera.x, self.rect.y - camera.y))