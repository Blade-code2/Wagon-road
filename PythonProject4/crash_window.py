import random
import time
from Helpers import *
from Main import *


# ---------------- CRASH WINDOW ----------------

def run_crash_window():
    screen.fill(CRASH_BG)

    base_error_lines = [
        "Unhandled exception 0xC0000005 at 0x0047AF12",
        "The instruction at 0x0047AF12 referenced memory at 0x00000000.",
        "The memory could not be \"read\".",
        "Debug info: npc_awareness_flag set unexpectedly (0x01)"
    ]

    running = True
    glitch_timer = 0
    jitter = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        glitch_timer += 1
        if glitch_timer % 10 == 0:
            jitter = random.randint(-2, 2)

        screen.fill(CRASH_BG)

        y = HEIGHT // 3 + jitter
        for line in base_error_lines:
            draw_text(screen, line, font_small, TEXT_COLOR, LEFT_COL + jitter, y)
            y += 30

        draw_text(screen, "Click the close button to exit.", font_small, TEXT_COLOR_DIM, LEFT_COL, y + 40)

        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.display.quit()


# ---------------- ENTITY MESSAGE ----------------

def run_entity_message():
    delay = random.uniform(2.0, 6.0)
    time.sleep(delay)

    pygame.display.init()
    global screen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    msg = "ENTITY ERROR: TERMINATED — SUBJECT REMOVED"

    start_time = time.time()
    show_time = 4.0

    running = True
    while running:
        elapsed = time.time() - start_time
        if elapsed > show_time:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR_NORMAL)
        draw_text(screen, msg, font_main, TEXT_COLOR, LEFT_COL, HEIGHT // 2)
        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.display.quit()

