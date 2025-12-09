import pygame

# Initialize Pygame
pygame.init()

# Create a display window
screen = pygame.display.set_mode((1400, 800))
pygame.display.set_caption("Ford Fulkerson Algorithm Visualization")

# Constant definitions
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BG_COLOR = (54, 69, 79)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
NODE_RADIUS = 20

# Variables
editing_node = None
moving_node = None

source_node = None
sink_node = None

nodes = []

# Class definitions
class Node:
    def __init__(self, x, y, radius):
        self.center = (x, y)
        self.radius = radius

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, self.center, self.radius+2) # Draw border
        col = WHITE
        if self == moving_node:
            col = GREEN
        elif self == editing_node:
            col = GRAY
        elif self == source_node:
            col = BLUE
        elif self == sink_node:
            col = RED
        pygame.draw.circle(surface, col, self.center, self.radius) # Draw node

# Logic Function definitions

# Helpers
def collides(node_a, node_b):
    dist = ((node_a.center[0] - node_b.center[0]) ** 2 + (node_a.center[1] - node_b.center[1]) ** 2) ** 0.5
    return dist < node_a.radius + node_b.radius + 5

def get_node_selected(event):
    for node in nodes:
        # Unpack center coordinates
        cx, cy = node.center
        
        # Calculate distance from click to center
        dx = event.pos[0] - cx
        dy = event.pos[1] - cy
        distance = (dx**2 + dy**2)**0.5
        
        if distance < node.radius:
            print(f"Node at {node.center} selected")
            return node
    return None


def update_node_position():
    global moving_node
    is_collision = False
    
    if moving_node:
        mx, my = pygame.mouse.get_pos()
        
        temp_node = Node(mx, my, moving_node.radius)
        for node in nodes:
            if node != moving_node and collides(node, temp_node):
                is_collision = True
                break
        
        if not is_collision:
            moving_node.center = (mx, my)

        if not pygame.mouse.get_pressed()[0]:  # Left mouse button released
            moving_node = None


# UI Methods
def add_node(event):
    x, y = event.pos
    new_node = Node(x, y, NODE_RADIUS)
    for node in nodes:
        if collides(node, new_node):
            return
            
    nodes.append(new_node)

def delete_node():
    global source_node, sink_node, editing_node
    if editing_node in nodes:
        if editing_node == source_node:
            source_node = None
        if editing_node == sink_node:
            sink_node = None
        nodes.remove(editing_node)
        print(f"Node at {editing_node.center} deleted")
        editing_node = None

# Graphical Function definitions
def draw_scene():
    screen.fill(BG_COLOR)  # Fill screen with charcoal Black
    for node in nodes:
        node.draw(screen)

# ========================== Game loop ========================== #

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                editing_node = moving_node = get_node_selected(event)

            elif event.button == 3:  # Right mouse button
                add_node(event)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and editing_node:
                source_node = editing_node
                print(f"Source node set at {source_node.center}")

            elif event.key == pygame.K_k and editing_node:
                sink_node = editing_node
                print(f"Sink node set at {sink_node.center}")
            
            elif (event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE) and editing_node:
                delete_node()

            editing_node = None

        update_node_position()
    
    # Draw everything
    draw_scene()
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
