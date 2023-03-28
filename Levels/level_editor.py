import pygame
import pickle
import os
import json
import os.path

pygame.init()

# Setting screen variables
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
LEFT_SECTION = 250
RIGHT_SECTION = 250
TOP_SECTION = 40
BOTTOM_SECTION = 80
OBS_TYPE = 25
FTR_TYPE = 4
BLOCK_TYPE = OBS_TYPE+FTR_TYPE
BLOCK_SIZE = 40
MAX_COLUMNS = 100
MAX_ROWS = 16
LEVEL = 1
LASER_SELECTING = False
toggle_point = ()
font = pygame.font.SysFont('impact', 30)
screen = pygame.display.set_mode((LEFT_SECTION+SCREEN_WIDTH+RIGHT_SECTION, TOP_SECTION+SCREEN_HEIGHT+BOTTOM_SECTION))
pygame.display.set_caption('')
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1
current_block = 0
tmp_cols = MAX_COLUMNS
reset_map_confirmation = False
rewrite_confirmation = False
EOF = False
EOF_counter = 0

# Defining Colors
RED = (255, 77, 64)
GREEN = (80, 200, 120)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DIM_GRAY = (105, 105, 105)
WHITE = (255, 255, 255)
BLANCHED_ALMOND = (255, 235, 205)


# Resetting the map for reuse
def reset_map():
    map_data = []
    for x in range(MAX_ROWS):
        r = [-1] * (MAX_COLUMNS + RIGHT_SECTION // BLOCK_SIZE)
        map_data.append(r)
    for x in range(0, MAX_COLUMNS + RIGHT_SECTION // BLOCK_SIZE):
        map_data[MAX_ROWS - 1][x] = 0
        map_data[0][x] = 0
    for y in range(0, 16):
        map_data[y][0] = 0
        map_data[y][MAX_COLUMNS - 1] = 0

    return map_data


laser_select_list = []


def laser_bind_add():
    if os.path.exists(f"levels_laser/level{LEVEL}.json"):
        with open(f"levels_laser/level{LEVEL}.json", "r") as f:
            laser_existing_list = json.load(f)
        with open(f"levels_laser/level{LEVEL}.json", "w") as f:
            is_saved = -1
            for x, l in enumerate(laser_existing_list):
                if l[0] == list(toggle_point):
                    is_saved = x
            if is_saved >= 0:
                laser_existing_list[is_saved] = [list(toggle_point)] + laser_select_list
                json.dump(laser_existing_list, f)
            else:
                laser_existing_list.append([list(toggle_point)] + laser_select_list)
                json.dump(laser_existing_list, f)
    else:
        with open(f"levels_laser/level{LEVEL}.json", "w") as f:
            laser_existing_list = []
            laser_existing_list.append([list(toggle_point)] + laser_select_list)
            json.dump(laser_existing_list, f)
    pickle_out = open(f'levels_data/level{LEVEL}_data', 'wb')
    print(len(map_save(map_data)[0]))
    pickle.dump(map_save(map_data), pickle_out)
    pickle_out.close()


def laser_bind_delete():
    with open(f"levels_laser/level{LEVEL}.json", "r") as f:
        laser_existing_list = json.load(f)
    with open(f"levels_laser/level{LEVEL}.json", "w") as f:
        pos = -1
        for x, l in enumerate(laser_existing_list):
            print(l[0], list(toggle_point))
            if l[0] == list(toggle_point):
                poa = x
        laser_existing_list.remove(laser_existing_list[pos])
        print(laser_existing_list)
        json.dump(laser_existing_list, f)


# Drawing obstacles for the map
def draw_map():
    for y, row in enumerate(map_data):
        for x, block in enumerate(row):
            if block >= 0:
                screen.blit(img_list[block], (x * BLOCK_SIZE+RIGHT_SECTION - scroll, y * BLOCK_SIZE+TOP_SECTION))


# Drawing functions
def draw_section():
    pygame.draw.rect(screen, DIM_GRAY, (0, TOP_SECTION, LEFT_SECTION, SCREEN_HEIGHT))    # Left Section
    pygame.draw.rect(screen, DIM_GRAY, (LEFT_SECTION+SCREEN_WIDTH, TOP_SECTION,    # Right Section
                                               RIGHT_SECTION, SCREEN_HEIGHT))
    pygame.draw.rect(screen, DIM_GRAY, (0, 0,                # Top Section
                                               LEFT_SECTION+SCREEN_WIDTH+RIGHT_SECTION, TOP_SECTION))
    pygame.draw.rect(screen, DIM_GRAY, (0, TOP_SECTION+SCREEN_HEIGHT,   # Bottom Section
                                               LEFT_SECTION+SCREEN_WIDTH+RIGHT_SECTION-1, BOTTOM_SECTION))
    pygame.draw.line(screen, WHITE, (0, TOP_SECTION), (LEFT_SECTION+SCREEN_WIDTH+RIGHT_SECTION, TOP_SECTION))  # Line 1
    pygame.draw.line(screen, WHITE, (0, TOP_SECTION+SCREEN_HEIGHT),  # Line 2
                     (LEFT_SECTION + SCREEN_WIDTH + RIGHT_SECTION, TOP_SECTION+SCREEN_HEIGHT))
    pygame.draw.line(screen, WHITE, (RIGHT_SECTION, TOP_SECTION),  # Line 3
                     (RIGHT_SECTION, TOP_SECTION+SCREEN_HEIGHT))
    pygame.draw.line(screen, WHITE, (LEFT_SECTION+SCREEN_WIDTH, TOP_SECTION),  # Line 4
                     (LEFT_SECTION + SCREEN_WIDTH, TOP_SECTION+SCREEN_HEIGHT))


# Drawing texts
def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


# Drawing grids for the level editor
def draw_grid():
    for c in range(MAX_COLUMNS + 1):
        pygame.draw.line(screen, WHITE, (c * BLOCK_SIZE + RIGHT_SECTION - scroll, TOP_SECTION),
                         (c * BLOCK_SIZE + RIGHT_SECTION - scroll, SCREEN_HEIGHT+TOP_SECTION))
    for c in range(MAX_ROWS + 1):
        pygame.draw.line(screen, WHITE, (RIGHT_SECTION, c * BLOCK_SIZE), (RIGHT_SECTION+SCREEN_WIDTH, c * BLOCK_SIZE))


# All update functions is in here
def update_screen():
    screen.fill(BLACK)
    draw_grid()
    draw_map()
    draw_section()
    draw_text('Obstacles', font, BLACK, 65, 55)
    draw_text('Features', font, BLACK, SCREEN_WIDTH + RIGHT_SECTION + 75, 55)
    draw_text(f'scroll_speed : {scroll_speed}', font, BLACK, 65, 0)
    draw_text(f'scroll : {scroll+800}', font, BLACK, 300, 0)
    draw_text(f'Map size : {MAX_COLUMNS} columns', font, BLACK, 500, 0)
    if not reset_map_confirmation:
        draw_text(f'Reset map : {tmp_cols} columns', font, BLACK, 20, TOP_SECTION+SCREEN_HEIGHT+20)
    else:
        draw_text(f'This will reset all map, click to confirm :', font, BLACK, 20, TOP_SECTION+SCREEN_HEIGHT+20)
    if EOF:
        draw_text(f'Error of file, not found.', font, BLACK, 700, TOP_SECTION + SCREEN_HEIGHT + 20)
    else:
        if not rewrite_confirmation:
            draw_text(f'Current level : {LEVEL}', font, BLACK, 620, TOP_SECTION + SCREEN_HEIGHT + 20)
        else:
            draw_text(f'File already exist, do you want to rewrite it?', font, BLACK, 600, TOP_SECTION+SCREEN_HEIGHT+20)
    if LASER_SELECTING:
        draw_text(f'Save & rewrite lasers : ', font, BLACK, 900, 0)


# Cutting unnecessary cols
def map_save(map_data):
    data = []
    if len(map_data[0]) > MAX_COLUMNS:
        for row in range(MAX_ROWS):
            r = []
            for col in range(len(map_data[0])-(RIGHT_SECTION // BLOCK_SIZE)):
                r.append(map_data[row][col])
            data.append(r)
        return data
    return map_data


# Generate button
class CreateButton:
    def __init__(self, x, y, img, scale):
        self.width = img.get_width()
        self.height = img.get_height()          # Resizing image
        self.img = pygame.transform.scale(img, (int(self.width * scale), int(self.height * scale)))
        self.rect = self.img.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self):
        triggered = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0] and not self.clicked:
            triggered = True
            self.clicked = True
        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False
        screen.blit(self.img, (self.rect.x, self.rect.y))
        return triggered


# Load images
img_list = []
for x in range(BLOCK_TYPE):
    img = pygame.image.load(f'../imgs/blocks/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (BLOCK_SIZE, BLOCK_SIZE))
    img_list.append(img)
plus_img = pygame.image.load("../imgs/functional/plus.png").convert_alpha()
minus_img = pygame.image.load("../imgs/functional/minus.png").convert_alpha()
set_img = pygame.image.load("../imgs/functional/set.png").convert_alpha()
confirm_img = pygame.image.load("../imgs/functional/confirm.png").convert_alpha()
cancel_img = pygame.image.load("../imgs/functional/cancel.png").convert_alpha()
save_img = pygame.image.load("../imgs/functional/save.png").convert_alpha()
load_img = pygame.image.load("../imgs/functional/load.png").convert_alpha()


# Generating buttons for selecting blocks
btn_list = []
row = col = 0
for i in range(OBS_TYPE):
    block_button = CreateButton(col * 55 + 20, TOP_SECTION + 80 + row * 50, img_list[i], 1)
    btn_list.append(block_button)
    col += 1
    if col == 4:
        row += 1
        col = 0
row = col = 0
for i in range(FTR_TYPE):
    block_button = CreateButton(col * 55 + 1070, TOP_SECTION + 80 + row * 50, img_list[i+OBS_TYPE], 1)
    btn_list.append(block_button)
    col += 1
    if col == 4:
        row += 1
        button_col = 0

# Other buttons
col_increment = CreateButton(330, TOP_SECTION+SCREEN_HEIGHT+25, plus_img, 1)
col_decrement = CreateButton(370, TOP_SECTION+SCREEN_HEIGHT+25, minus_img, 1)
set_btn = CreateButton(450, TOP_SECTION+SCREEN_HEIGHT+10, set_img, 2)
l_confirm_btn = CreateButton(520, TOP_SECTION+SCREEN_HEIGHT+25, confirm_img, 1)
l_cancel_btn = CreateButton(560, TOP_SECTION+SCREEN_HEIGHT+25, cancel_img, 1)
save_btn = CreateButton(950, TOP_SECTION+SCREEN_HEIGHT+20, save_img, 1.5)
load_btn = CreateButton(1010, TOP_SECTION+SCREEN_HEIGHT+20, load_img, 1.5)
r_confirm_btn = CreateButton(1150, TOP_SECTION+SCREEN_HEIGHT+25, confirm_img, 1)
r_cancel_btn = CreateButton(1190, TOP_SECTION+SCREEN_HEIGHT+25, cancel_img, 1)
level_increment = CreateButton(850, TOP_SECTION+SCREEN_HEIGHT+25, plus_img, 1)
level_decrement = CreateButton(890, TOP_SECTION+SCREEN_HEIGHT+25, minus_img, 1)
laser_confirm_btn = CreateButton(1190, 3, confirm_img, 1)
laser_cancel_btn = CreateButton(1240, 3, cancel_img, 1)


# ------------------------ Main Loop ------------------------
map_data = reset_map()
run = True
while run:

    update_screen()

    # scroll the map
    if scroll_left:
        scroll -= 5 * scroll_speed
    if scroll_right:
        scroll += 5 * scroll_speed
    if scroll < 0:
        scroll = 0
    if scroll > MAX_COLUMNS * BLOCK_SIZE - SCREEN_WIDTH:
        scroll = MAX_COLUMNS * BLOCK_SIZE - SCREEN_WIDTH

    # Buttons
    for i, button in enumerate(btn_list):
        if button.draw():
            current_block = i
        pygame.draw.rect(screen, WHITE, btn_list[current_block].rect, 2)
    # Laser
    if LASER_SELECTING:
        if laser_confirm_btn.draw():
            laser_bind_add()
            LASER_SELECTING = False
        if laser_cancel_btn.draw():
            LASER_SELECTING = False
            map_data[toggle_point[0]][toggle_point[1]] = -1
    # Resetting map
    if not reset_map_confirmation:
        if col_increment.draw():
            tmp_cols += 1
        if col_decrement.draw() and tmp_cols > 20:
            tmp_cols -= 1
        if tmp_cols != MAX_COLUMNS:
            if set_btn.draw():
                reset_map_confirmation = True
    else:
        if l_confirm_btn.draw():
            reset_map_confirmation = False
            MAX_COLUMNS = tmp_cols
            map_data = reset_map()
        if l_cancel_btn.draw():
            reset_map_confirmation = False
    if not EOF:
        if not rewrite_confirmation:
            if level_increment.draw():
                LEVEL += 1
            if level_decrement.draw():
                if LEVEL > 1:
                    LEVEL -= 1
            if save_btn.draw():
                if os.path.isfile(f"levels_data/level{LEVEL}_data"):
                    rewrite_confirmation = True
                else:
                    pickle_out = open(f'levels_data/level{LEVEL}_data', 'wb')
                    pickle.dump(map_save(map_data), pickle_out)
                    print(map_save(map_data)[0])
                    pickle_out.close()
            if load_btn.draw():
                if os.path.isfile(f"levels_data/level{LEVEL}_data"):
                    scroll = 0
                    map_data = []
                    pickle_in = open(f'levels_data/level{LEVEL}_data', 'rb')
                    map_data = pickle.load(pickle_in)
                    pickle_in.close()
                    print(map_data)
                    MAX_COLUMNS = tmp_cols = len(map_data[0])
                    # print(map_data)
                else:
                    EOF = True
        else:
            if r_confirm_btn.draw():
                pickle_out = open(f'levels_data/level{LEVEL}_data', 'wb')
                pickle.dump(map_save(map_data), pickle_out)
                pickle_out.close()
                rewrite_confirmation = False
            if r_cancel_btn.draw():
                rewrite_confirmation = False
    # File not found
    else:
        EOF_counter += 1
        if EOF_counter > 100:
            EOF_counter = 0
            EOF = False

    pos = pygame.mouse.get_pos()
    x = int((pos[0] - LEFT_SECTION + scroll) // BLOCK_SIZE)  # Col been selected
    y = int(pos[1] // BLOCK_SIZE - TOP_SECTION // BLOCK_SIZE)    # Row been selected

    if (LEFT_SECTION < pos[0] - scroll % BLOCK_SIZE < LEFT_SECTION + SCREEN_WIDTH) and\
            (TOP_SECTION < pos[1] < TOP_SECTION+SCREEN_HEIGHT):
            if LASER_SELECTING:
                if pygame.mouse.get_pressed()[0] == 1 and (map_data[y][x] == 27 or map_data[y][x] == 28):
                    if [y, x] not in laser_select_list:
                        laser_select_list.append([y, x])
                pygame.draw.circle(screen, (220, 60, 20), (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]), 10)
            else:
                if pygame.mouse.get_pressed()[0] == 1:
                    if map_data[y][x] != current_block:
                        map_data[y][x] = current_block
                        if current_block == 26:
                            LASER_SELECTING = True
                            toggle_point = (y, x)
                            laser_select_list = []
                if pygame.mouse.get_pressed()[2] == 1:
                    if map_data[y][x] == 26:
                        toggle_point = (y, x)
                        laser_bind_delete()
                    map_data[y][x] = -1

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 3
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1

    pygame.display.update()
pygame.quit()
