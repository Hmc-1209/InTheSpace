import pygame
import os
import random
import pickle
import json
import math
import time
from pygame import mixer

from GlobalVariables import screen_height, screen_width, scroll_thresh
from particles import particles
from CreateButton import CreateButton

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
levels = len(os.listdir("Levels/levels_data"))
main = True
scroll_point = scroll_thresh()
MAX_LEVELS = 2
screen_scroll = 0
screen_scroll_player2 = 0
bg_scroll = 0
start_game = False
start_intro = False
level_complete = False
font = pygame.font.SysFont('impact', 30)
start_fade_sig = 0
fading = False

pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
COLS = len(pickle.load(pickle_in)[0])
pickle_in.close()

particle1_group = []
laser_group = pygame.sprite.Group()
toggle_group = pygame.sprite.Group()
mobileplatform_group = pygame.sprite.Group()

# Defining colors and fonts
RED = (255, 0, 0)
DARK_SILVER = (154, 154, 154)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

# ------------------------ Defining player action variables ------------------------
player_moving_left = False
player_moving_right = False
player2_moving_left = False
player2_moving_right = False


# ------------------------ Loading map images ------------------------
img_list = []
for x in range(BLOCK_TYPES-1):
    img = pygame.image.load(f'imgs/blocks/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (BLOCK_SIZE, BLOCK_SIZE))
    img_list.append(img)

map_data = []

bg_img = []
for i in range(4):
    bg_img.append(pygame.transform.scale(pygame.image.load(f"imgs/background/{i}.png"), (screen_height(), screen_height())))

title_img = pygame.transform.scale(pygame.image.load("imgs/title.png").convert_alpha(), (600, 200))
level_img = pygame.transform.scale(pygame.image.load("imgs/level.png").convert_alpha(), (400, 100))
start_img = pygame.transform.scale(pygame.image.load("imgs/start.png").convert_alpha(), (400, 100))
quit_img = pygame.transform.scale(pygame.image.load("imgs/quit.png").convert_alpha(), (400, 100))
next_img = pygame.transform.scale(pygame.image.load("imgs/next.png").convert_alpha(), (40, 40))
prev_img = pygame.transform.scale(pygame.image.load("imgs/prev.png").convert_alpha(), (40, 40))
fade_img = pygame.transform.scale(pygame.image.load("imgs/fade.png").convert_alpha(), (screen_width(), screen_height()))
dead_aud = pygame.mixer.Sound("audio/dead.mp3")
dead_aud.set_volume(.1)


def draw_bg():
    screen.fill(BLACK)
    r = math.ceil(COLS * BLOCK_SIZE / screen_height())
    width = bg_img[0].get_width()
    for i in range(r):
        pass
        screen.blit(bg_img[0], (i * width - bg_scroll * 0.5, 0))
        # screen.blit(bg_img[1], (i * width - bg_scroll * 0.7, 0))
        # screen.blit(bg_img[2], (i * width - bg_scroll * 0.5, 0))
        screen.blit(bg_img[3], (i * width - bg_scroll * 0.5, 0))


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
            frames = len(os.listdir(f"imgs/character/{char_type}/{animation}"))
            for f in range(frames-1):
                img = pygame.image.load(f"imgs/character/{char_type}/{animation}/{f}.png")
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
            if (self.char_type == 'player' and (player_moving_left or player_moving_right)) or\
                    (self.char_type == 'player2' and (player2_moving_left or player2_moving_right)):
                self.update_action(1)
            elif self.in_air:
                pass
            else:
                self.update_action(0)

    def move(self):
        dx = dy = 0
        d_screen_scroll = 0
        if not fading:
            if (self.char_type == 'player' and player_moving_left) or (self.char_type == 'player2' and player2_moving_left):
                dx = -self.speed
                self.flip = True
                self.direction = -1
            if (self.char_type == 'player' and player_moving_right) or (self.char_type == 'player2' and player2_moving_right):
                dx = self.speed
                self.flip = False
                self.direction = 1
            if self.jump and not self.in_air:
                self.vel_y = -12
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
                        dy = block[1].bottom - self.rect.top

                    elif self.vel_y >= 0:
                        self.in_air = False
                        dy = block[1].top - self.rect.bottom
                    self.vel_y = 0

            for toggle in toggle_group:
                if toggle.rect.colliderect(self.rect.x, self.rect.y, self.image.get_width(), self.image.get_height()) and not toggle.is_toggled:
                    toggle.is_toggled = True
                    toggle.image = toggle.imgs[1]
                    delete_laser(toggle.pointX, toggle.pointY)

            for mb in mobileplatform_group:
                if mb.rect.colliderect(self.rect.x + dx, self.rect.y, self.image.get_width(), self.image.get_height()):
                    if mb.direction == -1:
                        self.rect.y -= 3
                    dx = 0
                if mb.rect.colliderect(self.rect.x, self.rect.y + dy, self.image.get_width(), self.image.get_height()):
                    if self.vel_y < 0:
                        self.vel_y = 0
                        dy = mb.rect.bottom - self.rect.top
                    elif self.vel_y >= 0:
                        self.vel_y = 0
                        self.in_air = False
                        dy = mb.rect.top - self.rect.bottom

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
            elif self.char_type == 'player2':
                if player.is_alive:
                    if self.rect.left + dx < 0 or self.rect.right + dx > screen_width():
                        self.rect.x -= dx
                else:
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
                    pygame.image.load(f"imgs/laser/horizontal/{i}.png"), (40, 30)).convert_alpha())
            else:
                self.imgs.append(pygame.transform.scale(
                    pygame.image.load(f"imgs/laser/vertical/{i}.png"), (30, 40)).convert_alpha())
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


class MobilePlatform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x * BLOCK_SIZE + bg_scroll
        self.y = y * BLOCK_SIZE
        self.start_counter = random.randint(100, 150)
        self.start_point = self.x
        self.end_point = self.x - 4 * BLOCK_SIZE
        self.direction = -1
        self.image = pygame.transform.scale(pygame.image.load("imgs/mobileplatform/0.png").convert_alpha(), (40, 40))
        self.rect = self.image.get_rect()
        self.rect.midtop = (self.x + BLOCK_SIZE // 2, self.y + (BLOCK_SIZE - self.image.get_height()) // 2)

    def update(self):
        self.rect.x += screen_scroll
        self.start_point += screen_scroll
        self.end_point += screen_scroll
        if self.start_counter == 0:
            if self.direction == -1:
                if self.rect.x > self.end_point:
                    self.rect.x -= 1
                else:
                    self.direction *= -1
            else:
                if self.rect.x < self.start_point:
                    self.rect.x += 1
                else:
                    self.direction *= -1
        else:
            self.start_counter -= 1

    def draw(self):
        if self.start_counter == 0:
            screen.blit(self.image, self.rect)


class Entrance(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x * BLOCK_SIZE
        self.y = y * BLOCK_SIZE
        self.imgs = []
        for i in range(3):
            self.imgs.append(pygame.transform.scale(pygame.image.load(f"imgs/entrance/{i}.png"), (40, 40)).convert_alpha())
        self.frame = 0
        self.update_time = 0
        self.image = self.imgs[0]
        self.rect = self.image.get_rect()
        self.rect.midtop = (self.x + BLOCK_SIZE // 2, self.y + (BLOCK_SIZE - self.image.get_height()) // 2)

    def update(self):
        Animation_Cooldown = 150
        if pygame.time.get_ticks() - self.update_time > Animation_Cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame += 1
            if self.frame == 3:
                self.frame = 0
            self.image = self.imgs[self.frame]
        self.rect.x += screen_scroll
        if pygame.sprite.collide_rect(self, player) or pygame.sprite.collide_rect(self, player2):
            level_complete = True
            return level_complete

    def draw(self):
        screen.blit(self.image, self.rect)


class Transition(pygame.sprite.Sprite):
    def __init__(self, type, color, step):
        pygame.sprite.Sprite.__init__(self)
        self.counter = 0
        self.finish = False
        self.type = type
        self.color = color
        self.step = step

    def update(self):
        if self.type == 0:
            pygame.draw.rect(screen, self.color, (0+self.step, screen_width(), 0, screen_height()))
        self.step += 1


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
                if [laser.pointY, laser.pointX] == [i[0], i[1]]:
                    laser_group.remove(laser)


class Map:
    def __init__(self):
        self.obstacle_list = []
        self.decoration_list = []
        self.wire_end_list = []
        self.playerX = 0
        self.playerY = 0
        self.player2X = 0
        self.player2Y = 0
        self.level_length = 0

    def process_data(self, data):
        group_clear()
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
                    elif block == 29:  # Setting player position values
                        self.player2X = x * BLOCK_SIZE
                        self.player2Y = y * BLOCK_SIZE
                    elif block == 30:
                        mb = MobilePlatform(x, y)
                        mobileplatform_group.add(mb)
                    elif block == 31:
                        entrance = Entrance(x, y)

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
        player2 = Character(self.player2X, self.player2Y, 1, 7, 'player2', 5)
        return player, player2, entrance

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
                particle1_group.append([[block[1][0]+20, block[1][1]+25], [random.randint(10, 30) / 10 - 2, -1],
                                        random.randint(1, 4), block[1][0]+20, (60, 20, 20), (255, 140, 0)])
        particles(screen, particle1_group, screen_scroll)


class Fade:
    def __init__(self, dir, color):
        self.fade_counter = 0
        self.dir = dir
        self.color = color

    def fade(self):
        fade_complete = False

        # Fade in
        if self.dir == 1:
            pygame.draw.rect(screen, self.color, (0, 0, self.fade_counter, screen_height()))
            self.fade_counter += 30

            if self.fade_counter >= screen_width():
                fade_complete = True

        # Fade out
        if self.dir == 2:
            pygame.draw.rect(screen, self.color, (self.fade_counter, 0, screen_width(), screen_height()))
            self.fade_counter += 30

            if self.fade_counter >= screen_width():
                fade_complete = True

        return fade_complete


# ------------------------ Main loop ------------------------
IN_THE_SPACE = True
fade_in = Fade(1, DARK_SILVER)
fade_out = Fade(2, DARK_SILVER)


def reset_level():
    mobileplatform_group.empty()
    toggle_group.empty()
    laser_group.empty()
    player.kill()
    player2.kill()
    entrance.kill()


def next_level():
    reset_level()
    map = Map()
    player, player2, entrance = map.process_data(map_data)
    return player, player2, entrance, map


def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def group_clear():
    for laser in laser_group:
        laser_group.remove(laser)
    for toggle in toggle_group:
        toggle_group.remove(toggle)
    particle1_group.clear()


# Music
def bg_music(n):
    pygame.mixer.music.fadeout(800)
    pygame.mixer.music.unload()
    pygame.mixer.music.load(f"audio/BG_{n}.mp3")
    pygame.mixer.music.play(-1, 0, 0)
    pygame.mixer.music.set_volume(.05)


bg_music(1)
while IN_THE_SPACE:
    clock.tick(FPS)
    if not main:
        draw_bg()
        map.draw()

        # ------------------------ Checking movements for both player ------------------------
        if player.is_alive and player2.is_alive:
            screen_scroll_tmp, level_complete = player.move()
            screen_scroll_player2 = screen_scroll_tmp - screen_scroll
            screen_scroll = screen_scroll_tmp
            player2.move()
            player2.rect.x += screen_scroll
        elif player2.is_alive:
            screen_scroll, level_complete = player2.move()
        elif player.is_alive:
            screen_scroll, level_complete = player.move()

        # ------------------------ Calling updating functions ------------------------
        bg_scroll -= screen_scroll

        if player.is_alive:
            player.draw()
            player.update()
        if player2.is_alive:
            player2.draw()
            player2.update()
        for toggle in toggle_group:
            toggle.update()
            toggle.draw()
        for mb in mobileplatform_group:
            mb.update()
            mb.draw()

        # Checking if player touched any laser
        if pygame.sprite.spritecollideany(player, laser_group):
            dead_aud.play()
            for i in range(100):
                particle1_group.append(
                    [[player.rect.x + 30 * player.direction, player.rect.y + 20 + random.randint(-30, 10)],
                     [random.randint(0, 30) / 10 - 2, -1], random.randint(4, 7), 20, (77, 128, 230), (30, 144, 255)])
            player.rect.y -= 1000
            player.is_alive = False
            player_moving_right = player_moving_left = screen_scroll = False
        elif pygame.sprite.spritecollideany(player2, laser_group):
            dead_aud.play()
            for i in range(100):
                particle1_group.append(
                    [[player2.rect.x + 30 * player2.direction, player2.rect.y + 20 + random.randint(-30, 10)],
                     [random.randint(0, 30) / 10 - 2, -1], random.randint(4, 7), 20, (60, 20, 20), (220, 20, 60)])
            player2.rect.y -= 1000
            player2.is_alive = False
            player2_moving_right = player2_moving_left = screen_scroll = False

        if (player2.rect.x <= 0 or player2.rect.x >= screen_width()) and player2.is_alive:
            dead_aud.play()
            for i in range(100):
                particle1_group.append(
                    [[player2.rect.x, player2.rect.y + random.randint(-30, 10)], [random.randint(0, 30) / 10 - 2, -1],
                     random.randint(4, 7), 20, (60, 20, 20), (220, 20, 60)])
            player2.rect.y -= 1000
            player2.is_alive = False
        entrance.draw()
        # Entrance behavior
        if entrance.update():
            start_fade_sig = 1
            if fade_in.fade():
                start_fade_sig = 2
                fade_in.fade_counter = 0
            if start_fade_sig == 2:
                LEVEL += 1
                if os.path.exists(f"Levels/levels_data/level{LEVEL}_data"):
                    pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
                    COLS = len(pickle.load(pickle_in)[0])
                    pickle_in.close()
                    pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
                    map_data = []
                    for i in range(16):
                        r = [-1] * COLS
                        map_data.append(r)
                    map_data = pickle.load(pickle_in)
                    pickle_in.close()
                    player, player2, entrance, map = next_level()
                    screen_scroll = screen_scroll_player2 = 0
                    bg_scroll = 0
                else:
                    player_moving_right = player_moving_left = player2_moving_right = player2_moving_left = False
                    screen_scroll = screen_scroll_player2 = bg_scroll = 0
                    LEVEL -= 1
                    main = True

        # Check if all player dies
        if not player.is_alive and not player2.is_alive:
            reset_level()
            screen_scroll = bg_scroll = 0
            main = True

        if start_fade_sig == 1:
            pygame.mixer.music.fadeout(800)
            fading = True

        if start_fade_sig == 2:
            draw_text("Loading", font, RED, 30, screen_height() - 40)
            if fade_out.fade():
                bg_music(2)
                fading = False
                fade_out.fade_counter = 0
                start_fade_sig = 0
        # ------------------------ Button events ------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                IN_THE_SPACE = False
            # Keyboard presses
            if event.type == pygame.KEYDOWN:
                if player.is_alive and not fading:
                    if event.key == pygame.K_a:
                        player_moving_left = True
                    if event.key == pygame.K_d:
                        player_moving_right = True
                    if event.key == pygame.K_w:
                        player.in_air = True
                        player.jump = True
                    if event.key == pygame.K_ESCAPE:
                        IN_THE_SPACE = False
                if player2.is_alive and not fading:
                    if event.key == pygame.K_j:
                        player2_moving_left = True
                    if event.key == pygame.K_l:
                        player2_moving_right = True
                    if event.key == pygame.K_i:
                        player2.in_air = True
                        player2.jump = True
            # Keyboard released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player_moving_left = False
                if event.key == pygame.K_d:
                    player_moving_right = False
                if event.key == pygame.K_j:
                    player2_moving_left = False
                if event.key == pygame.K_l:
                    player2_moving_right = False
    else:
        screen.fill(BLACK)
        screen.blit(title_img, (screen_width() / 2 - title_img.get_width() / 2, 20))
        level_btn = CreateButton(screen_width() / 2 - level_img.get_width() / 2, 250, level_img, 1)
        start_btn = CreateButton(screen_width() / 2 - start_img.get_width() / 2, 350, start_img, 1)
        quit_btn = CreateButton(screen_width() / 2 - quit_img.get_width() / 2, 450, quit_img, 1)
        next_btn = CreateButton(screen_width() / 2 - level_img.get_width() / 2 + 450, 280, next_img, 1)
        prev_btn = CreateButton(screen_width() / 2 - level_img.get_width() / 2 - 100, 280, prev_img, 1)

        level_btn.draw(screen)
        draw_text(f"{LEVEL}", font, WHITE, screen_width() / 2 - level_img.get_width() / 2 + 320, 280)
        if next_btn.draw(screen):
            if LEVEL < levels:
                LEVEL += 1
                time.sleep(.1)
        if prev_btn.draw(screen):
            if LEVEL > 1:
                LEVEL -= 1
                time.sleep(.1)
        if start_btn.draw(screen):
            start_fade_sig = 1
        if quit_btn.draw(screen):
            IN_THE_SPACE = False

        # Starting the game (fade)
        if start_fade_sig == 1 and fade_in.fade():
            fade_in.fade_counter = 0
            start_fade_sig = 2
            pygame.mixer.music.fadeout(800)
            main = False
            for i in range(16):
                r = [-1] * COLS
                map_data.append(r)
            pickle_in = open(f'Levels/levels_data/level{LEVEL}_data', 'rb')
            map_data = pickle.load(pickle_in)
            pickle_in.close()
            group_clear()
            map = Map()
            player, player2, entrance = map.process_data(map_data)

        if start_fade_sig == 2:
            draw_text("Loading", font, RED, 30, screen_height() - 40)
            if fade_out.fade():
                bg_music(1)
                fading = False
                fade_out.fade_counter = 0
                start_fade_sig = 0

    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            IN_THE_SPACE = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            IN_THE_SPACE = False

    pygame.display.update()

pygame.quit()
