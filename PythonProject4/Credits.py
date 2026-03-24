import pygame
import sys

def run_credits():
    pygame.init()

    # --- FULLSCREEN MODE ---
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()

    pygame.display.set_caption("Credits")
    clock = pygame.time.Clock()

    # --- Your credits text embedded directly ---
    credits_lines = [
        "Wagon Game – Credits",
        "",
        "Programming:",
        "Me",
        "Still me",
        "Me but slightly more caffeinated",
        "Me at 3:01AM realising I broke something",
        "Me at 3:02AM pretending I didn’t",
        "",
        "Art & Design:",
        "Also me",
        "Me but with Canva open in another tab",
        "Me googling 'how to draw wagon' at 2AM",
        "",
        "Writing:",
        "Me at 3AM",
        "Me at 3:01AM",
        "Me at 3:01:30AM rewriting everything",
        "Me at 3:02AM giving up and keeping the first draft",
        "",
        "Special Thanks:",
        "My ADHD for the hyperfocus arc",
        "My spine for not resigning mid‑project",
        "My computer for surviving (barely)",
        "You, the player, for actually finishing this",
        "Energy drinks that stopped me from breaking down in tears"

    ]

    # --- Font setup ---
    font = pygame.font.SysFont("Consolas", 32)  # terminal vibe

    # Render each line into a surface (WHITE TEXT)
    rendered_lines = [font.render(line, True, (255, 255, 255)) for line in credits_lines]

    # Starting Y position (begin below the screen)
    start_y = HEIGHT

    # --- Create scanline overlay surface ---
    scanlines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):  # every 4 pixels
        pygame.draw.line(scanlines, (0, 0, 0, 70), (0, y), (WIDTH, y))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

        screen.fill((0, 0, 0))

        # Draw each line with spacing
        y = start_y
        for surf in rendered_lines:
            x = (WIDTH - surf.get_width()) // 2
            screen.blit(surf, (x, y))
            y += 50  # vertical spacing

        # Move the whole block upward
        start_y -= 1  # scroll speed

        # When the last line scrolls off the top, exit
        if y < 0:
            running = False

        # --- Draw scanlines on top ---
        screen.blit(scanlines, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()