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
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
NODE_RADIUS = 20

# Variables
editing_node = None
moving_node = None
edge_start_node = None  # Node where edge creation started
selected_edge = None  # Currently selected edge
pending_edge = None  # Edge waiting for capacity input
input_text = ""  # Text input for edge capacity
input_active = False  # Whether input dialog is active

source_node = None
sink_node = None

nodes = []
edges = []  # List to store edges

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
        elif self == edge_start_node:
            col = YELLOW
        pygame.draw.circle(surface, col, self.center, self.radius) # Draw node

class Edge:
    def __init__(self, node_from, node_to, capacity=10):
        self.node_from = node_from
        self.node_to = node_to
        self.capacity = capacity
        self.flow = 0

    def draw(self, surface):
        # Draw arrow from node_from to node_to
        start_pos = self.node_from.center
        end_pos = self.node_to.center
        
        # Choose color based on selection
        color = ORANGE if self == selected_edge else WHITE
        line_width = 4 if self == selected_edge else 2
        
        # Draw line
        pygame.draw.line(surface, color, start_pos, end_pos, line_width)
        
        # Draw arrowhead
        import math
        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        arrow_length = 15
        arrow_angle = math.pi / 6
        
        # Calculate arrow endpoint (on the edge of target node)
        arrow_end_x = end_pos[0] - self.node_to.radius * math.cos(angle)
        arrow_end_y = end_pos[1] - self.node_to.radius * math.sin(angle)
        
        # Calculate arrowhead points
        left_x = arrow_end_x - arrow_length * math.cos(angle - arrow_angle)
        left_y = arrow_end_y - arrow_length * math.sin(angle - arrow_angle)
        right_x = arrow_end_x - arrow_length * math.cos(angle + arrow_angle)
        right_y = arrow_end_y - arrow_length * math.sin(angle + arrow_angle)
        
        pygame.draw.polygon(surface, color, [
            (arrow_end_x, arrow_end_y),
            (left_x, left_y),
            (right_x, right_y)
        ])
        
        # Draw flow/capacity label
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        
        font = pygame.font.Font(None, 26)
        flow_text = f"{self.flow}/{self.capacity}"
        text = font.render(flow_text, True, YELLOW)
        text_rect = text.get_rect(center=(mid_x, mid_y))
        
        # Draw background for text
        padding = 6
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(surface, BLACK, bg_rect)
        pygame.draw.rect(surface, color, bg_rect, 2)
        
        surface.blit(text, text_rect)

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

def get_node_at_pos(pos):
    """Get node at given position"""
    for node in nodes:
        cx, cy = node.center
        dx = pos[0] - cx
        dy = pos[1] - cy
        distance = (dx**2 + dy**2)**0.5
        
        if distance < node.radius:
            return node
    return None

def get_edge_selected(pos):
    """Check if click is near an edge"""
    click_x, click_y = pos
    threshold = 10  # Distance threshold for selecting edge
    
    for edge in edges:
        x1, y1 = edge.node_from.center
        x2, y2 = edge.node_to.center
        
        # Calculate distance from point to line segment
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_length_sq == 0:
            continue
        
        # Calculate projection parameter
        t = max(0, min(1, ((click_x - x1) * (x2 - x1) + (click_y - y1) * (y2 - y1)) / line_length_sq))
        
        # Calculate closest point on line segment
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # Calculate distance from click to closest point
        dist = ((click_x - proj_x)**2 + (click_y - proj_y)**2)**0.5
        
        if dist < threshold:
            print(f"Edge selected from {edge.node_from.center} to {edge.node_to.center}")
            return edge
    
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
        
        # Remove edges connected to this node
        edges[:] = [e for e in edges if e.node_from != editing_node and e.node_to != editing_node]
        
        nodes.remove(editing_node)
        print(f"Node at {editing_node.center} deleted")
        editing_node = None

def delete_edge():
    global selected_edge
    if selected_edge in edges:
        edges.remove(selected_edge)
        print(f"Edge from {selected_edge.node_from.center} to {selected_edge.node_to.center} deleted")
        selected_edge = None

def add_edge(node_from, node_to):
    """Add edge between two nodes with capacity input"""
    global pending_edge, input_active, input_text
    
    # Check if edge already exists
    for edge in edges:
        if edge.node_from == node_from and edge.node_to == node_to:
            print("Edge already exists")
            return
    
    # Create pending edge and activate input
    pending_edge = {'from': node_from, 'to': node_to}
    input_active = True
    input_text = ""
    print(f"Enter capacity for edge from {node_from.center} to {node_to.center}")

def confirm_edge():
    """Confirm edge creation with entered capacity"""
    global pending_edge, input_active, input_text
    
    if pending_edge and input_text.isdigit() and int(input_text) > 0:
        capacity = int(input_text)
        new_edge = Edge(pending_edge['from'], pending_edge['to'], capacity)
        edges.append(new_edge)
        print(f"Edge created with capacity {capacity}")
    else:
        print("Invalid capacity. Edge not created.")
    
    pending_edge = None
    input_active = False
    input_text = ""

def cancel_edge():
    """Cancel edge creation"""
    global pending_edge, input_active, input_text
    pending_edge = None
    input_active = False
    input_text = ""
    print("Edge creation cancelled")

# Graphical Function definitions
def draw_scene():
    screen.fill(BG_COLOR)  # Fill screen with charcoal Black
    
    # Draw edges first (so they appear behind nodes)
    for edge in edges:
        edge.draw(screen)
    
    # Draw temporary edge line while creating
    if edge_start_node and pygame.mouse.get_pressed()[2]:
        pygame.draw.line(screen, YELLOW, edge_start_node.center, pygame.mouse.get_pos(), 2)
    
    # Draw nodes
    for node in nodes:
        node.draw(screen)
    
    # Draw input dialog if active
    if input_active:
        draw_input_dialog()

def draw_input_dialog():
    """Draw the enhanced capacity input dialog"""
    dialog_width = 450
    dialog_height = 200
    dialog_x = (screen.get_width() - dialog_width) // 2
    dialog_y = (screen.get_height() - dialog_height) // 2
    
    # Draw shadow
    shadow_offset = 5
    pygame.draw.rect(screen, (20, 20, 20), 
                    (dialog_x + shadow_offset, dialog_y + shadow_offset, dialog_width, dialog_height),
                    border_radius=10)
    
    # Draw dialog background with gradient effect
    pygame.draw.rect(screen, (40, 50, 60), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=10)
    pygame.draw.rect(screen, (100, 150, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=10)
    
    # Draw title bar
    title_bar_height = 50
    pygame.draw.rect(screen, (60, 80, 100), (dialog_x, dialog_y, dialog_width, title_bar_height), 
                    border_top_left_radius=10, border_top_right_radius=10)
    
    # Draw title with icon
    font_title = pygame.font.Font(None, 36)
    title_text = font_title.render(" Edge Capacity", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 25))
    screen.blit(title_text, title_rect)
    
    # Draw prompt text
    font_prompt = pygame.font.Font(None, 24)
    prompt_text = font_prompt.render("Enter the maximum flow capacity:", True, (200, 200, 200))
    prompt_rect = prompt_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 70))
    screen.blit(prompt_text, prompt_rect)
    
    # Draw input box with glow effect
    input_box_width = 350
    input_box_height = 50
    input_box_x = dialog_x + (dialog_width - input_box_width) // 2
    input_box_y = dialog_y + 95
    
    # Glow effect
    for i in range(3):
        glow_alpha = 50 - i * 15
        glow_rect = pygame.Rect(input_box_x - i * 2, input_box_y - i * 2, 
                               input_box_width + i * 4, input_box_height + i * 4)
        pygame.draw.rect(screen, (100, 150, 200, glow_alpha), glow_rect, 2, border_radius=8)
    
    # Input box background
    pygame.draw.rect(screen, (30, 40, 50), (input_box_x, input_box_y, input_box_width, input_box_height), 
                    border_radius=8)
    pygame.draw.rect(screen, (150, 200, 255), (input_box_x, input_box_y, input_box_width, input_box_height), 
                    2, border_radius=8)
    
    # Draw input text
    input_font = pygame.font.Font(None, 42)
    display_text = input_text if input_text else "0"
    input_surface = input_font.render(display_text, True, (255, 255, 255))
    input_text_rect = input_surface.get_rect(center=(input_box_x + input_box_width // 2, 
                                                      input_box_y + input_box_height // 2))
    screen.blit(input_surface, input_text_rect)
    
    # Draw blinking cursor if input is active
    if pygame.time.get_ticks() % 1000 < 500:  # Blink every 500ms
        cursor_x = input_text_rect.right + 5
        cursor_y = input_box_y + 10
        pygame.draw.line(screen, (255, 255, 255), 
                        (cursor_x, cursor_y), 
                        (cursor_x, cursor_y + input_box_height - 20), 2)
    
    # Draw buttons with hover effect
    button_y = dialog_y + 160
    
    # OK Button
    ok_button_rect = pygame.Rect(dialog_x + 80, button_y, 150, 35)
    ok_color = (50, 200, 50) if input_text.isdigit() and int(input_text) > 0 else (100, 100, 100)
    pygame.draw.rect(screen, ok_color, ok_button_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, ok_button_rect, 2, border_radius=5)
    
    ok_font = pygame.font.Font(None, 28)
    ok_text = ok_font.render(" OK (Enter)", True, WHITE)
    ok_text_rect = ok_text.get_rect(center=ok_button_rect.center)
    screen.blit(ok_text, ok_text_rect)
    
    # Cancel Button
    cancel_button_rect = pygame.Rect(dialog_x + 250, button_y, 150, 35)
    pygame.draw.rect(screen, (200, 50, 50), cancel_button_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, cancel_button_rect, 2, border_radius=5)
    
    cancel_text = ok_font.render(" Cancel (Esc)", True, WHITE)
    cancel_text_rect = cancel_text.get_rect(center=cancel_button_rect.center)
    screen.blit(cancel_text, cancel_text_rect)

# ========================== Game loop ========================== #

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle input dialog separately
        elif input_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    confirm_edge()
                elif event.key == pygame.K_ESCAPE:
                    cancel_edge()
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit():
                    input_text += event.unicode
        
        # Normal event handling
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                node = get_node_selected(event)
                if node:
                    editing_node = moving_node = node
                    selected_edge = None  # Deselect edge when selecting node
                else:
                    # Check if clicking on an edge
                    selected_edge = get_edge_selected(event.pos)
                    editing_node = None  # Deselect node when selecting edge

            elif event.button == 3:  # Right mouse button
                node = get_node_selected(event)
                if node:
                    # Start edge creation
                    edge_start_node = node
                    print(f"Edge creation started from {node.center}")
                else:
                    # Add node if not clicking on existing node
                    add_node(event)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3 and edge_start_node:  # Right mouse button released
                end_node = get_node_at_pos(event.pos)
                if end_node and end_node != edge_start_node:
                    add_edge(edge_start_node, end_node)
                edge_start_node = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and editing_node:
                source_node = editing_node
                print(f"Source node set at {source_node.center}")

            elif event.key == pygame.K_k and editing_node:
                sink_node = editing_node
                print(f"Sink node set at {sink_node.center}")
            
            elif (event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE):
                if editing_node:
                    delete_node()
                elif selected_edge:
                    delete_edge()

            editing_node = None

        if not input_active:
            update_node_position()
    
    # Draw everything
    draw_scene()
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()