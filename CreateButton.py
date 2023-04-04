import pygame


# Generate button
class CreateButton:
    def __init__(self, x, y, img, scale):
        self.width = img.get_width()
        self.height = img.get_height()          # Resizing image
        self.img = pygame.transform.scale(img, (int(self.width * scale), int(self.height * scale)))
        self.rect = self.img.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, screen):
        triggered = False
        pos = pygame.mouse.get_pos()
        self.img.set_alpha(200)
        if self.rect.collidepoint(pos):
            self.img.set_alpha(250)
            if pygame.mouse.get_pressed()[0] and not self.clicked:
                triggered = True
                self.clicked = True
        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False
        screen.blit(self.img, (self.rect.x, self.rect.y))
        return triggered