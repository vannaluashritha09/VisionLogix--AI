import pygame

# Initialize Pygame
pygame.init()

# Create a window
screen = pygame.display.set_mode((800, 600))

# Set the window title
pygame.display.set_caption("VisionLogix-AI Test")

# Set the background color to white
screen.fill((255, 255, 255))

# Update the display
pygame.display.flip()

# Keep the window open
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()