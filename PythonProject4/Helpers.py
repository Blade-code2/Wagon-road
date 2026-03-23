import os
import pygame
import sys


# ---------------- GLOBAL CONFIG ----------------
WIDTH, HEIGHT = 0, 0  # will be set after fullscreen init
FPS = 60

# Monochrome terminal style
BG_COLOR_NORMAL = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_DIM = (180, 180, 180)
TEXT_COLOR_HORROR = (255, 0, 0)
CRASH_BG = (0, 0, 0)

MINIMAP_BG = (20, 20, 20)
MINIMAP_FILL = (255, 255, 255)
MINIMAP_BORDER = (120, 120, 120)

TOTAL_DISTANCE = 1000
LUCID_TRIGGER_DISTANCE = 800
MAX_LOG_LINES = 7

# File system config
GAME_DATA_DIR = "game_data"
STATE_FILE = os.path.join(GAME_DATA_DIR, "state.json")
NPC_FILES = {
    "Mara": os.path.join(GAME_DATA_DIR, "passenger_mara.mem"),
    "Jon": os.path.join(GAME_DATA_DIR, "passenger_jon.mem"),
    "Eli": os.path.join(GAME_DATA_DIR, "passenger_eli.mem"),
}
SUPPRESSOR_FILE = os.path.join(GAME_DATA_DIR, "entity_suppressor.sys")

pygame.init()

# Fullscreen terminal-style window
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Wagon Road")

clock = pygame.time.Clock()
font_main = pygame.font.SysFont("consolas", 24)
font_small = pygame.font.SysFont("consolas", 18)
font_big = pygame.font.SysFont("consolas", 32)

LEFT_COL = 40
RIGHT_COL = WIDTH // 2 + 40
BOTTOM_LOG_Y = HEIGHT - 200


# ---------------- HELPERS ----------------

def draw_text(surface, text, font, color, x, y, center=False):
    lines = text.split("\n")
    offset_y = 0
    for line in lines:
        surf = font.render(line, True, color)
        rect = surf.get_rect()
        if center:
            rect.topleft = (x - rect.width // 2, y + offset_y)
        else:
            rect.topleft = (x, y + offset_y)
        surface.blit(surf, rect)
        offset_y += rect.height + 4


def draw_minimap(surface, distance):
    progress = max(0.0, min(1.0, distance / TOTAL_DISTANCE))
    bar_x = LEFT_COL
    bar_y = 20
    bar_w = WIDTH - LEFT_COL * 2
    bar_h = 16

    pygame.draw.rect(surface, MINIMAP_BG, (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(surface, MINIMAP_BORDER, (bar_x, bar_y, bar_w, bar_h), 2)

    fill_w = int(bar_w * progress)
    if fill_w > 0:
        pygame.draw.rect(surface, MINIMAP_FILL, (bar_x + 1, bar_y + 1, fill_w - 2, bar_h - 2))

    percent = int(progress * 100)
    txt = f"Route progress: {percent}%"
    draw_text(surface, txt, font_small, TEXT_COLOR_DIM, bar_x, bar_y + 22)


def draw_scanlines(surface):
    for y in range(0, HEIGHT, 3):
        pygame.draw.line(surface, (0, 0, 0), (0, y), (WIDTH, y), 1)


def wait_for_key():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return
        clock.tick(FPS)

