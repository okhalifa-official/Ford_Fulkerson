import pygame
# Initialize Pygame
pygame.init()
# Create a display window
screen = pygame.display.set_mode((1400, 800))
pygame.display.set_caption("Ford Fulkerson Algorithm Visualization")

# Game loop
running = True
clock = pygame.time.Clock()

class GraphObject:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Node:
    def __init__(self, x, y, radius, color):
        self.center = (x, y)
        self.radius = radius
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.center, self.radius)

objs = [
]

node_color = [(0, 0, 255),(255,0,0), (255,255,255)]

def draw_scene():
    screen.fill((54, 69, 79))  # Fill screen with charcoal Black
    for obj in objs:
        obj.draw(screen)

def add_node(event):
    x, y = event.pos
    new_node = Node(x, y, 20, node_color[min(len(objs),2)])
    for obj in objs:
        if isinstance(obj, Node):
            dist = ((obj.center[0] - x) ** 2 + (obj.center[1] - y) ** 2) ** 0.5
            if dist < obj.radius + new_node.radius:
                return  # Prevent overlapping nodes
            
    objs.append(new_node)

def select_node(event):
    for obj in objs:
        # Unpack center coordinates
        cx, cy = obj.center
        
        # Calculate distance from click to center
        dx = event.pos[0] - cx
        dy = event.pos[1] - cy
        distance = (dx**2 + dy**2)**0.5
        
        if distance < obj.radius:
            print(f"Node at {obj.center} selected")
            obj.color = (0, 255, 0)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                add_node(event)
            elif event.button == 3:  # Right mouse button
                select_node(event)
    
    draw_scene()
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
