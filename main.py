import pygame

# Initialize Pygame
pygame.init()

# Create a display window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Game")

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0, 0, 0))  # Fill screen with black
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()