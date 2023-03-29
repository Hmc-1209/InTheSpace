import pygame
import os
import random
import pickle
import json
from pygame import mixer

from GlobalVariables import screen_height, screen_width, scroll_thresh

# Initialize the pygame
pygame.init()
mixer.init()

# ------------------------ Create the screen ------------------------
SCREEN_WIDTH = screen_width()
SCREEN_HEIGHT = screen_height()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('InTheSpace')

# Setting frame rate
clock = pygame.time.Clock()
FPS = 70

# ------------------------ Game variables ------------------------
GRAVITY = 0.75
ROWS = 16
BLOCK_SIZE = SCREEN_HEIGHT // ROWS
BLOCK_TYPES = len(os.listdir("imgs/blocks"))
LEVEL = 1
scroll_point = scroll_thresh()
MAX_LEVELS = 2
screen_scroll = 0
bg_scroll = 0
start_game = False
start_intro = False
level_complete = False

pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
COLS = len(pickle.load(pickle_in)[0])
pickle_in.close()

particle1_group = []
laser_group = pygame.sprite.Group()
toggle_group = pygame.sprite.Group()

# Defining colors and fonts
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

# ------------------------ Defining player action variables ------------------------
moving_left = False
moving_right = False


# ------------------------ Loading map images ------------------------
img_list = []
for x in range(BLOCK_TYPES-2):
    img = pygame.image.load(f'imgs/blocks/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (BLOCK_SIZE, BLOCK_SIZE))
    img_list.append(img)

map_data = []
for i in range(16):
    r = [-1] * COLS
    map_data.append(r)
pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
map_data = pickle.load(pickle_in)
pickle_in.close()


# ------------------------ Particles ------------------------
def circle_surf(radius, color):
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf


def particles():
    for particle in particle1_group:
        particle[0][0] += particle[1][0] + screen_scroll
        particle[0][1] += particle[1][1]
        particle[2] -= 0.1
        particle[1][1] += 0.2
        particle[3] += screen_scroll

        if not (particle[0][0] < 0 or particle[0][0] > SCREEN_WIDTH):
            pygame.draw.circle(screen, (255, 140, 0), [int(particle[0][0]), int(particle[0][1])], int(particle[2]))

        radius = particle[2] * 2
        screen.blit(circle_surf(radius, (60, 20, 20)), (int(particle[0][0] - radius), int(particle[0][1] - radius)),
                    special_flags=pygame.BLEND_RGB_ADD)
        if particle[2] <= 0 or particle[0][0] < 0 or particle[0][0] > SCREEN_WIDTH:
            particle1_group.remove(particle)


# ------------------------ Objects ------------------------
class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, speed, char_type, health):
        pygame.sprite.Sprite.__init__(self)
        self.animationsList = []
        self.is_alive = True
        self.speed = speed
        self.action = 0
        self.health = health
        self.frameIndex = 0
        self.flip = False
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.char_type = char_type
        self.in_air = False
        self.ANIMATION_COOLDOWN = 100
        self.update_time = pygame.time.get_ticks()

        # Load Images
        animations = ["idle", "move"]
        for animation in animations:
            tmpL = []
            frames = len(os.listdir(f"imgs/character/player/{animation}"))
            for f in range(frames-1):
                img = pygame.image.load(f"imgs/character/player/{animation}/{f}.png")
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                tmpL.append(img)
            self.animationsList.append(tmpL)

        self.image = self.animationsList[self.action][0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update_animation(self):
        self.image = self.animationsList[self.action][self.frameIndex]
        if pygame.time.get_ticks() - self.update_time > self.ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frameIndex += 1
            if self.frameIndex >= len(self.animationsList[self.action]):
                self.frameIndex = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frameIndex = 0
            self.update_time = pygame.time.get_ticks()

    def update(self):
        self.update_animation()
        if self.is_alive:
            if moving_left or moving_right:
                self.update_action(1)
            elif self.in_air:
                pass
            else:
                self.update_action(0)

    def move(self):
        dx = dy = 0
        d_screen_scroll = 0
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        if self.jump and not self.in_air:
            self.vel_y = -15
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom += 50
            self.health = 0

        for block in map.obstacle_list:
            if block[1].colliderect(self.rect.x + dx, self.rect.y, self.image.get_width(), self.image.get_height()):
                dx = 0
                if self.char_type == 'enemy':
                    self.direction *= -1
            if block[1].colliderect(self.rect.x, self.rect.y + dy, self.image.get_width(), self.image.get_height()):
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = block[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = block[1].top - self.rect.bottom

        for toggle in toggle_group:
            if toggle.rect.colliderect(self.rect.x, self.rect.y, self.image.get_width(), self.image.get_height()) and not toggle.is_toggled:
                delete_laser(toggle.pointX, toggle.pointY)
                toggle.is_toggled = True
                toggle.image = toggle.imgs[1]

        self.rect.x += dx
        self.rect.y += dy

        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > screen_width():
                dx = 0
            if (self.rect.right > SCREEN_WIDTH - scroll_point and
                bg_scroll < (map.level_length * BLOCK_SIZE) - SCREEN_WIDTH) or \
                self.rect.left < scroll_point and bg_scroll > abs(dx):
                self.rect.x -= dx
                d_screen_scroll = -dx

        return d_screen_scroll, level_complete

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, dir):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.pointX = x / BLOCK_SIZE
        self.pointY = y / BLOCK_SIZE
        self.imgs = []
        self.frames = random.randint(0, 2)
        self.update_time = pygame.time.get_ticks()
        for i in range(3):
            if dir == 0:
                self.imgs.append(pygame.transform.scale(
                    pygame.image.load(f"imgs/laser/horizontal/{i}.png"), (40, 40)).convert_alpha())
            else:
                self.imgs.append(pygame.transform.scale(
                    pygame.image.load(f"imgs/laser/vertical/{i}.png"), (40, 40)).convert_alpha())
        self.image = self.imgs[self.frames]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + BLOCK_SIZE // 2, y + (BLOCK_SIZE - self.image.get_height()) // 2)

    def update(self):
        Animation_Cooldown = 150
        self.image = self.imgs[self.frames]
        if pygame.time.get_ticks() - self.update_time > Animation_Cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frames += 1
            if self.frames >= 3:
                self.frames = 0
        self.rect.x += screen_scroll

    def draw(self):
        screen.blit(self.image, self.rect)


class Toggle(pygame.sprite.Sprite):
    def __init__(self, x, y, related_lasers):
        pygame.sprite.Sprite.__init__(self)
        self.x = x * BLOCK_SIZE
        self.y = y * BLOCK_SIZE
        self.pointX = x
        self.pointY = y
        self.is_toggled = False
        self.related_lasers = related_lasers
        self.imgs = [pygame.transform.scale(pygame.image.load("imgs/toggles/0.png").convert_alpha(), (40, 40)),
                     pygame.transform.scale(pygame.image.load("imgs/toggles/1.png").convert_alpha(), (40, 40))]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect()
        self.rect.midtop = (self.x + BLOCK_SIZE // 2, self.y + (BLOCK_SIZE - self.image.get_height()) // 2)

    def update(self):
        self.rect.x += screen_scroll

    def draw(self):
        screen.blit(self.image, self.rect)


def delete_laser(toggle_pointX, toggle_pointY):
    with open(f"Levels/levels_laser/level{LEVEL}.json", "r") as f:
        points = json.load(f)
        delete = []
        for point in points:
            if point[1] == [toggle_pointY, toggle_pointX]:
                for i in range(2, len(point)):
                    delete.append(point[i])
        for i in delete:
            for laser in laser_group:
                print(laser.pointY, laser.pointX, i[0], i[1])
                if [laser.pointY, laser.pointX] == [i[0], i[1]]:
                    laser_group.remove(laser)
                print()


class Map:
    def __init__(self):
        self.obstacle_list = []
        self.decoration_list = []
        self.wire_end_list = []
        self.playerX = 0
        self.playerY = 0
        self.level_length = 0

    def process_data(self, data):
        self.level_length = len(data[0])
        for y, row in enumerate(data):
            for x, block in enumerate(row):
                if block >= 0:
                    img = img_list[block]
                    img_rect = img.get_rect()
                    img_rect.x = x * BLOCK_SIZE - screen_scroll
                    img_rect.y = y * BLOCK_SIZE
                    block_data = (img, img_rect)
                    if 8 <= block <= 13:
                        self.decoration_list.append(block_data)
                    elif 14 <= block <= 17:
                        self.wire_end_list.append(block_data)
                    elif block <= 24:
                        self.obstacle_list.append(block_data)
                    elif block == 25:  # Setting player position values
                        self.playerX = x * BLOCK_SIZE
                        self.playerY = y * BLOCK_SIZE

        with open(f"Levels/levels_laser/level{LEVEL}.json", "r") as f:
            points = json.load(f)
            for i in points:
                points_list = []
                for j in range(2, len(i)):
                    laser = Laser(i[j][1] * BLOCK_SIZE, i[j][0] * BLOCK_SIZE, i[0])
                    laser_group.add(laser)
                    points_list.append(i[j])
                toggle = Toggle(i[1][1], i[1][0], points_list)
                toggle_group.add(toggle)

        # Generating player and return
        player = Character(self.playerX, self.playerY, 1, 7, 'player', 5)
        return player

    def draw(self):
        for laser in laser_group:
            laser.update()
            laser.draw()
        for block in self.obstacle_list:
            block[1][0] += screen_scroll
            screen.blit(block[0], block[1])
        for block in self.decoration_list:
            block[1][0] += screen_scroll
            screen.blit(block[0], block[1])
        for block in self.wire_end_list:
            block[1][0] += screen_scroll
            screen.blit(block[0], block[1])
            if 0 < block[1][0] < SCREEN_WIDTH:
                particle1_group.append([[block[1][0]+20, block[1][1]+25], [random.randint(10, 30) / 10 - 2, -1], random.randint(1, 4), block[1][0]+20])
        particles()


# ------------------------ Main loop ------------------------
IN_THE_SPACE = True
map = Map()
player = map.process_data(map_data)

while IN_THE_SPACE:

    clock.tick(FPS)
    screen.fill(BLACK)
    map.draw()
    screen_scroll, level_complete = player.move()
    bg_scroll -= screen_scroll
    player.draw()
    player.update()
    for toggle in toggle_group:
        toggle.update()
        toggle.draw()

    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            IN_THE_SPACE = False
        # Keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_w:
                player.in_air = True
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                IN_THE_SPACE = False
        # Keyboard released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False

    pygame.display.update()

pygame.quit()
