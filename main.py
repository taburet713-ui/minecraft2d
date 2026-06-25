import pygame
import random
import json
import os
import sys

pygame.init()

# ================= SCREEN =================
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

TILE = 32
WORLD_W = 120
WORLD_H = 90

SAVE_FILE = "world_save.json"

# ================= BLOCKS =================
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4

colors = {
    AIR: (0, 0, 0),
    GRASS: (80, 200, 80),
    DIRT: (140, 90, 50),
    STONE: (130, 130, 130),
    WOOD: (120, 80, 40),
}

# ================= WORLD =================
def generate_world(flat=False):
    world = [[AIR for _ in range(WORLD_H)] for _ in range(WORLD_W)]

    for x in range(WORLD_W):
        ground = WORLD_H // 2 if flat else WORLD_H // 2 + random.randint(-2, 2)

        for y in range(WORLD_H):
            if y < ground:
                world[x][y] = AIR
            elif y == ground:
                world[x][y] = GRASS
            elif y <= ground + 4:
                world[x][y] = DIRT
            else:
                world[x][y] = STONE

    return world

world = generate_world(False)

# ================= SAVE =================
def save_world():
    with open(SAVE_FILE, "w") as f:
        json.dump(world, f)

def load_world():
    global world
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            world = json.load(f)

# ================= PLAYER =================
px, py = 20.0, 10.0
vy = 0.0
on_ground = False

PLAYER_W = 0.8
PLAYER_H = 1.8

# ================= MODE =================
MENU = 0
GAME = 1
mode = MENU
# ================= UI MENU BUTTONS =================
btn_new = pygame.Rect(350, 220, 300, 60)
btn_flat = pygame.Rect(350, 310, 300, 60)
btn_load = pygame.Rect(350, 400, 300, 60)

font = pygame.font.SysFont(None, 40)

def draw_menu():
    screen.fill((25, 25, 25))

    pygame.draw.rect(screen, (70, 140, 70), btn_new)
    pygame.draw.rect(screen, (70, 140, 70), btn_flat)
    pygame.draw.rect(screen, (70, 140, 70), btn_load)

    screen.blit(font.render("NEW WORLD", True, (255,255,255)), (410, 235))
    screen.blit(font.render("FLAT WORLD", True, (255,255,255)), (400, 325))
    screen.blit(font.render("LOAD WORLD", True, (255,255,255)), (405, 415))


# ================= PLAYER HOTBAR =================
hotbar = [GRASS, DIRT, STONE, WOOD]
selected = 0


# ================= CAMERA =================
cam_x = 0
cam_y = 0


# ================= JOYSTICK (FIXED INPUT VERSION) =================
joy_center = (120, HEIGHT - 140)
joy_radius = 60

joy_active = False
joy_dx = 0
joy_dy = 0


# ================= TOUCH BUTTONS =================
jump_btn = pygame.Rect(WIDTH - 140, HEIGHT - 140, 100, 100)


# ================= INPUT HANDLER =================
def handle_menu_click(pos):
    global mode, world, px, py, vy

    if btn_new.collidepoint(pos):
        world = generate_world(False)
        px, py, vy = 20, 10, 0
        mode = GAME

    if btn_flat.collidepoint(pos):
        world = generate_world(True)
        px, py, vy = 20, 10, 0
        mode = GAME

    if btn_load.collidepoint(pos):
        load_world()
        px, py, vy = 20, 10, 0
        mode = GAME


def handle_touch(pos):
    global vy, selected

    # jump
    if jump_btn.collidepoint(pos):
        if on_ground:
            vy = -4.5


# ================= JOYSTICK UPDATE (REAL FIX) =================
def update_joystick(pos, pressed):
    global joy_dx, joy_dy, joy_active

    if not pressed:
        joy_active = False
        joy_dx = 0
        joy_dy = 0
        return

    dx = pos[0] - joy_center[0]
    dy = pos[1] - joy_center[1]

    dist = (dx*dx + dy*dy) ** 0.5

    if dist < joy_radius:
        joy_active = True
        joy_dx = dx / joy_radius
        joy_dy = dy / joy_radius
    else:
        joy_active = True
        joy_dx = dx / dist
        joy_dy = dy / dist
        # ================= COLLISION =================
def collide(x, y):
    points = [
        (x, y),
        (x + PLAYER_W, y),
        (x, y + PLAYER_H),
        (x + PLAYER_W, y + PLAYER_H),
    ]

    for px_, py_ in points:
        ix = int(px_)
        iy = int(py_)

        if ix < 0 or iy < 0 or ix >= WORLD_W or iy >= WORLD_H:
            return True

        if world[ix][iy] != AIR:
            return True

    return False


# ================= MOVEMENT =================
def move(dx, dy=0):
    global px, py

    if not collide(px + dx, py):
        px += dx

    if not collide(px, py + dy):
        py += dy


# ================= PHYSICS =================
def physics():
    global py, vy, on_ground

    vy += 0.25
    vy *= 0.98

    if not collide(px, py + vy):
        py += vy
        on_ground = False
    else:
        vy = 0
        on_ground = True


# ================= BLOCK DRAW =================
def draw_block(x, y, t):
    pygame.draw.rect(screen, colors[t], (x, y, TILE, TILE))


# ================= TOUCH WORLD INTERACTION =================
def world_touch(pos):
    global world

    bx = int((pos[0] + cam_x) / TILE)
    by = int((pos[1] + cam_y) / TILE)

    if 0 <= bx < WORLD_W and 0 <= by < WORLD_H:

        # если есть блок → удалить
        if world[bx][by] != AIR:
            world[bx][by] = AIR

        # если пусто → поставить
        else:
            world[bx][by] = hotbar[selected]


# ================= GAME LOOP =================
running = True

while running:
    dt = clock.tick(60) / 1000
    screen.fill((135, 206, 235))

    cam_x = px * TILE - WIDTH // 2
    cam_y = py * TILE - HEIGHT // 2


    # ================= EVENTS =================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_world()
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if mode == MENU:
                handle_menu_click(event.pos)

            elif mode == GAME:
                handle_touch(event.pos)
                world_touch(event.pos)

        if event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                update_joystick(event.pos, True)

        if event.type == pygame.MOUSEBUTTONUP:
            update_joystick((0,0), False)


    # ================= GAME LOGIC =================
    if mode == GAME:

        # JOYSTICK MOVEMENT (FIXED)
        move(joy_dx * 0.2)

        physics()


        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            move(-0.15)
        if keys[pygame.K_d]:
            move(0.15)
        if keys[pygame.K_SPACE] and on_ground:
            vy = -4.5


    # ================= RENDER =================
    if mode == MENU:
        draw_menu()

    if mode == GAME:

        for x in range(int(px) - 20, int(px) + 20):
            for y in range(int(py) - 15, int(py) + 15):

                if 0 <= x < WORLD_W and 0 <= y < WORLD_H:

                    t = world[x][y]

                    if t != AIR:
                        sx = x * TILE - cam_x
                        sy = y * TILE - cam_y
                        draw_block(sx, sy, t)

        # player
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (px * TILE - cam_x, py * TILE - cam_y, TILE, TILE)
        )

        # joystick UI
        pygame.draw.circle(screen, (70,70,70), joy_center, joy_radius)
        pygame.draw.circle(
            screen,
            (200,200,200),
            (int(joy_center[0] + joy_dx * 40),
             int(joy_center[1] + joy_dy * 40)),
            25
        )

        # jump button
        pygame.draw.circle(screen, (240,220,80), jump_btn.center, 45)
        screen.blit(font.render("J", True, (0,0,0)),
                    (jump_btn.x + 35, jump_btn.y + 25))

    pygame.display.flip()

pygame.quit()
sys.exit()
