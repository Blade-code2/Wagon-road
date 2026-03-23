import os

import pygame

from Helpers import draw_text, font_main, TEXT_COLOR, clock


def run_credits():
    # Load credits text
    try:
        with open("Credits.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except:
        lines = ["Credits file missing.", "Add credits.txt to the game folder."]

    pygame.display.quit()
    pygame.display.init()

    WIDTH, HEIGHT = 800, 600
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Credits")

    # Start the text below the screen
    y = HEIGHT
    scroll_speed = 1  # pixels per frame

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        # Draw each line
        current_y = y
        for line in lines:
            draw_text(screen, line, font_main, TEXT_COLOR, WIDTH // 2, current_y, center=True)
            current_y += 40  # spacing between lines

        y -= scroll_speed

        # End when all text has scrolled off the top
        if current_y < 0:
            running = False

        pygame.display.flip()
        clock.tick(60)

