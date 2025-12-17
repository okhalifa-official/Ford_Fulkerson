import pygame
import math
from collections import deque

pygame.init()
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("Ford-Fulkerson Algorithm Visualization")

# Colors
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 100, 255)
BG_COLOR, BLACK, GRAY = (25, 30, 40), (0, 0, 0), (128, 128, 128)
WHITE, YELLOW, ORANGE = (255, 255, 255), (255, 220, 0), (255, 140, 0)
CYAN, PURPLE = (0, 255, 255), (180, 0, 255)
NODE_RADIUS = 25

# State variables
editing_node = moving_node = edge_start_node = selected_edge = pending_edge = None
input_text, input_active = "", False
source_node = sink_node = None
playing = play_used = step_requested = augmenting = simulation_done = False
speed_multiplier, augment_progress, current_bottleneck, total_flow = 1.0, 0.0, 0, 0
current_path, particles, augment_history = None, [], []
nodes, edges = [], []
animation_time = 0
_results_close_rect = None

class Node:
    def __init__(self, x, y, radius):
        self.center, self.radius = (x, y), radius

    def draw(self, surface):
        # Glow for source/sink
        if self == source_node or self == sink_node:
            glow_color = BLUE if self == source_node else RED
            for i in range(3):
                glow_radius = self.radius + 8 - i * 2
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*glow_color, 60 - i * 20), (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (self.center[0] - glow_radius, self.center[1] - glow_radius))
        
        pygame.draw.circle(surface, BLACK, self.center, self.radius + 3)
        
        col = (GREEN if self == moving_node else GRAY if self == editing_node else 
               BLUE if self == source_node else RED if self == sink_node else 
               YELLOW if self == edge_start_node else WHITE)
        
        pygame.draw.circle(surface, col, self.center, self.radius)
        pygame.draw.circle(surface, tuple(min(255, c + 40) for c in col), 
                         (self.center[0] - self.radius // 6, self.center[1] - self.radius // 6), self.radius // 4)
        
        if self == source_node or self == sink_node:
            font = pygame.font.Font(None, 20)
            text = font.render("S" if self == source_node else "T", True, WHITE)
            surface.blit(text, text.get_rect(center=self.center))

class Edge:
    def __init__(self, node_from, node_to, capacity=10):
        self.node_from, self.node_to = node_from, node_to
        self.capacity, self.flow = capacity, 0

    def draw(self, surface):
        start_pos, end_pos = self.node_from.center, self.node_to.center
        
        if self.flow == 0:
            color = (100, 100, 120)
        elif self.flow == self.capacity:
            color = (255, 50, 50)
        else:
            ratio = self.flow / self.capacity
            color = (255, int(255 - 100 * ratio), int(255 - 255 * ratio))
        
        if self == selected_edge:
            color = ORANGE
        
        line_width = 3 if self == selected_edge else 2
        pygame.draw.line(surface, color, start_pos, end_pos, line_width)

        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        arrow_end = (end_pos[0] - self.node_to.radius * math.cos(angle), 
                    end_pos[1] - self.node_to.radius * math.sin(angle))
        
        arrow_points = [arrow_end,
                       (arrow_end[0] - 15 * math.cos(angle - math.pi/6), 
                        arrow_end[1] - 15 * math.sin(angle - math.pi/6)),
                       (arrow_end[0] - 15 * math.cos(angle + math.pi/6), 
                        arrow_end[1] - 15 * math.sin(angle + math.pi/6))]
        pygame.draw.polygon(surface, color, arrow_points)

    def draw_label(self, surface):
        mid = ((self.node_from.center[0] + self.node_to.center[0]) / 2,
               (self.node_from.center[1] + self.node_to.center[1]) / 2)
        
        font = pygame.font.Font(None, 24)
        text = font.render(f"{self.flow}/{self.capacity}", True, YELLOW)
        text_rect = text.get_rect(center=mid)
        
        bg_rect = text_rect.inflate(16, 16)
        pygame.draw.rect(surface, (20, 25, 35), bg_rect, border_radius=4)
        pygame.draw.rect(surface, ORANGE if self == selected_edge else (80, 100, 120), bg_rect, 2, border_radius=4)
        surface.blit(text, text_rect)

class Particle:
    def __init__(self, edge, t=0.0, speed=0.01, color=CYAN):
        self.edge, self.t, self.speed, self.color = edge, t, speed, color

    def update(self, dt):
        self.t += self.speed * dt
        return self.t <= 1.0

    def draw(self, surface):
        x1, y1 = self.edge.node_from.center
        x2, y2 = self.edge.node_to.center
        px, py = x1 + (x2 - x1) * self.t, y1 + (y2 - y1) * self.t
        
        for i in range(2):
            glow_size = 5 + (2 - i) * 2
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 100 - i * 50), (glow_size, glow_size), glow_size)
            surface.blit(glow_surf, (int(px - glow_size), int(py - glow_size)))
        
        pygame.draw.circle(surface, self.color, (int(px), int(py)), 5)

def collides(node_a, node_b):
    return math.hypot(node_a.center[0] - node_b.center[0], node_a.center[1] - node_b.center[1]) < node_a.radius + node_b.radius + 5

def get_node_at_pos(pos):
    for node in nodes:
        if math.hypot(pos[0] - node.center[0], pos[1] - node.center[1]) < node.radius:
            return node
    return None

def get_edge_selected(pos):
    for edge in edges:
        x1, y1 = edge.node_from.center
        x2, y2 = edge.node_to.center
        line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_len_sq == 0:
            continue
        t = max(0, min(1, ((pos[0] - x1) * (x2 - x1) + (pos[1] - y1) * (y2 - y1)) / line_len_sq))
        proj = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        if math.hypot(pos[0] - proj[0], pos[1] - proj[1]) < 12:
            return edge
    return None

def draw_dashed_line(surface, color, start, end, width=1, dash=10):
    dist = math.hypot(end[0] - start[0], end[1] - start[1])
    if dist == 0:
        return
    dx, dy = (end[0] - start[0]) / dist, (end[1] - start[1]) / dist
    for i in range(0, int(dist / dash), 2):
        s = (start[0] + dx * i * dash, start[1] + dy * i * dash)
        e = (start[0] + dx * min((i+1) * dash, dist), start[1] + dy * min((i+1) * dash, dist))
        pygame.draw.line(surface, color, s, e, width)

def get_control_rects():
    btn_w, btn_h, offset = 110, 40, 80
    btn_x, btn_y = screen.get_width() - btn_w - 10 - offset, 10
    return {
        'play': pygame.Rect(btn_x, btn_y, btn_w, btn_h),
        'step': pygame.Rect(btn_x - 120, btn_y, 100, btn_h),
        'minus': pygame.Rect(btn_x - 160, btn_y + 6, 28, btn_h - 12),
        'plus': pygame.Rect(btn_x + btn_w + 6, btn_y + 6, 28, btn_h - 12),
        'quit': pygame.Rect(btn_x - 320, btn_y, 100, btn_h),
        'reset': pygame.Rect(btn_x - 450, btn_y, 100, btn_h),
    }

def update_node_position():
    global moving_node
    if moving_node and pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        temp = Node(mx, my, moving_node.radius)
        if not any(n != moving_node and collides(n, temp) for n in nodes):
            moving_node.center = (mx, my)
    elif moving_node:
        moving_node = None

def path_exists():
    if not source_node or not sink_node:
        return False
    adj = {n: [] for n in nodes}
    for e in edges:
        if e.capacity - e.flow > 0:
            adj[e.node_from].append(e.node_to)
    q = deque([source_node])
    visited = {source_node}
    while q:
        cur = q.popleft()
        if cur == sink_node:
            return True
        for nbr in adj.get(cur, []):
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)
    return False

def find_augmenting_path():
    if not source_node or not sink_node:
        return None, 0
    parent, q, visited = {}, deque([source_node]), {source_node}
    
    while q:
        u = q.popleft()
        if u == sink_node:
            break
        for e in edges:
            if e.node_from == u and e.capacity - e.flow > 0:
                if e.node_to not in visited:
                    visited.add(e.node_to)
                    parent[e.node_to] = (u, e, False)
                    q.append(e.node_to)
        for e in edges:
            if e.node_to == u and e.flow > 0:
                if e.node_from not in visited:
                    visited.add(e.node_from)
                    parent[e.node_from] = (u, e, True)
                    q.append(e.node_from)
    
    if sink_node not in parent:
        return None, 0
    
    path, node = [], sink_node
    while node != source_node:
        prev, edge, is_rev = parent[node]
        path.append((edge, is_rev))
        node = prev
    path.reverse()
    
    bottleneck = min((e.flow if is_rev else e.capacity - e.flow) for e, is_rev in path)
    return path, int(bottleneck)

def apply_augmentation(path, delta):
    for e, is_rev in path:
        e.flow += -delta if is_rev else delta

def spawn_particles(path, amount):
    for e, is_rev in path:
        if not is_rev:
            for i in range(min(8, max(2, amount))):
                particles.append(Particle(e, i / max(1, amount) * 0.3, 
                                        0.02 * speed_multiplier, CYAN))

def add_node(pos):
    new_node = Node(pos[0], pos[1], NODE_RADIUS)
    if not any(collides(n, new_node) for n in nodes):
        nodes.append(new_node)

def delete_node():
    global source_node, sink_node, editing_node
    if editing_node in nodes:
        if editing_node == source_node:
            source_node = None
        if editing_node == sink_node:
            sink_node = None
        edges[:] = [e for e in edges if e.node_from != editing_node and e.node_to != editing_node]
        nodes.remove(editing_node)
        editing_node = None

def delete_edge():
    global selected_edge
    if selected_edge in edges:
        edges.remove(selected_edge)
        selected_edge = None

def add_edge(node_from, node_to):
    global pending_edge, input_active, input_text
    if not any(e.node_from == node_from and e.node_to == node_to for e in edges):
        pending_edge, input_active, input_text = {'from': node_from, 'to': node_to}, True, ""

def confirm_edge():
    global pending_edge, input_active, input_text
    if pending_edge and input_text.isdigit() and int(input_text) > 0:
        edges.append(Edge(pending_edge['from'], pending_edge['to'], int(input_text)))
    pending_edge, input_active, input_text = None, False, ""

def cancel_edge():
    global pending_edge, input_active, input_text
    pending_edge, input_active, input_text = None, False, ""

def reset_simulation():
    global playing, play_used, augmenting, augment_progress, current_path, current_bottleneck
    global augment_history, simulation_done, total_flow, particles
    for e in edges:
        e.flow = 0
    playing = play_used = augmenting = simulation_done = False
    augment_progress = total_flow = current_bottleneck = 0
    current_path, augment_history, particles = None, [], []

def draw_scene():
    global animation_time
    animation_time += 1
    screen.fill(BG_COLOR)
    
    # Grid
    for x in range(0, screen.get_width(), 50):
        pygame.draw.line(screen, (35, 40, 50), (x, 0), (x, screen.get_height()))
    for y in range(0, screen.get_height(), 50):
        pygame.draw.line(screen, (35, 40, 50), (0, y), (screen.get_width(), y))
    
    for edge in edges:
        edge.draw(screen)
    
    if current_path:
        for e, is_rev in current_path:
            pulse = int(math.sin(animation_time * 0.1) * 2 + 6)
            if is_rev:
                draw_dashed_line(screen, (255, 120, 120), e.node_to.center, e.node_from.center, pulse, 12)
            else:
                pygame.draw.line(screen, (0, 220, 255), e.node_from.center, e.node_to.center, pulse)
    
    for edge in edges:
        edge.draw_label(screen)
    
    if edge_start_node and pygame.mouse.get_pressed()[2]:
        draw_dashed_line(screen, YELLOW, edge_start_node.center, pygame.mouse.get_pos(), 3, 15)
    
    for node in nodes:
        node.draw(screen)
    
    if input_active:
        draw_input_dialog()
    
    draw_controls()
    
    for e in edges:
        if e.flow > 0:
            draw_dashed_line(screen, (140, 140, 140), e.node_to.center, e.node_from.center, 2, 8)
    
    dt = clock.get_time() / 16.0
    for p in [p for p in particles if p.update(dt)]:
        p.draw(screen)
    particles[:] = [p for p in particles if p.t <= 1.0]
    
    if simulation_done:
        draw_results()
    elif not nodes and not input_active:
        draw_instructions()

def draw_instructions():
    font, y = pygame.font.Font(None, 28), screen.get_height() // 2 - 100
    for text in ["Right-click: Add nodes", "Right-click & drag: Create edges", 
                 "Left-click: Select", "Drag to move", "S: Set source", "K: Set sink", 
                 "Delete: Remove"]:
        rendered = font.render(text, True, (150, 160, 180))
        rect = rendered.get_rect(center=(screen.get_width() // 2, y))
        shadow = font.render(text, True, BLACK)
        screen.blit(shadow, (rect.x + 2, rect.y + 2))
        screen.blit(rendered, rect)
        y += 35

def draw_controls():
    rects = get_control_rects()
    enabled = path_exists() if source_node and sink_node else False
    font = pygame.font.Font(None, 28)
    
    # Play
    color = ((30, 150, 30) if playing else (60, 60, 60) if play_used or simulation_done 
            else (50, 200, 50) if enabled else (80, 80, 80))
    pygame.draw.rect(screen, color, rects['play'], border_radius=6)
    pygame.draw.rect(screen, WHITE, rects['play'], 2, border_radius=6)
    play_surf = font.render("Playing" if playing else "Play", True, WHITE)
    play_rect = play_surf.get_rect(center=rects['play'].center)
    screen.blit(play_surf, play_rect)
    
    # Step
    pygame.draw.rect(screen, (70, 130, 200), rects['step'], border_radius=6)
    pygame.draw.rect(screen, WHITE, rects['step'], 2, border_radius=6)
    step_surf = font.render("Step", True, WHITE)
    step_rect = step_surf.get_rect(center=rects['step'].center)
    screen.blit(step_surf, step_rect)
    
    # Speed
    for key in ['minus', 'plus']:
        pygame.draw.rect(screen, (100, 100, 100), rects[key], border_radius=6)
        pygame.draw.rect(screen, WHITE, rects[key], 2, border_radius=6)
        sym = "-" if key == 'minus' else "+"
        sym_surf = font.render(sym, True, WHITE)
        sym_rect = sym_surf.get_rect(center=rects[key].center)
        screen.blit(sym_surf, sym_rect)
    
    speed_surf = font.render(f"{speed_multiplier:.1f}x", True, WHITE)
    speed_rect = speed_surf.get_rect(center=(rects['minus'].left - 40, rects['minus'].centery))
    screen.blit(speed_surf, speed_rect)
    
    # Reset
    pygame.draw.rect(screen, (200, 140, 50), rects['reset'], border_radius=6)
    pygame.draw.rect(screen, WHITE, rects['reset'], 2, border_radius=6)
    reset_surf = font.render("Reset", True, WHITE)
    reset_rect = reset_surf.get_rect(center=rects['reset'].center)
    screen.blit(reset_surf, reset_rect)
    
    # Quit
    pygame.draw.rect(screen, (200, 50, 50), rects['quit'], border_radius=6)
    pygame.draw.rect(screen, WHITE, rects['quit'], 2, border_radius=6)
    quit_surf = font.render("Exit", True, WHITE)
    quit_rect = quit_surf.get_rect(center=rects['quit'].center)
    screen.blit(quit_surf, quit_rect)

def draw_input_dialog():
    w, h = 450, 200
    x, y = (screen.get_width() - w) // 2, (screen.get_height() - h) // 2
    
    pygame.draw.rect(screen, (0, 0, 0, 180), (x + 5, y + 5, w, h), border_radius=10)
    pygame.draw.rect(screen, (40, 50, 60), (x, y, w, h), border_radius=10)
    pygame.draw.rect(screen, (100, 150, 200), (x, y, w, h), 3, border_radius=10)
    pygame.draw.rect(screen, (60, 80, 100), (x, y, w, 50), border_top_left_radius=10, border_top_right_radius=10)
    
    title = pygame.font.Font(None, 36).render("Edge Capacity", True, WHITE)
    screen.blit(title, title.get_rect(center=(x + w // 2, y + 25)))
    
    prompt = pygame.font.Font(None, 24).render("Enter maximum flow capacity:", True, (200, 200, 200))
    screen.blit(prompt, prompt.get_rect(center=(x + w // 2, y + 70)))
    
    input_box = pygame.Rect(x + 50, y + 95, 350, 50)
    pygame.draw.rect(screen, (30, 40, 50), input_box, border_radius=8)
    pygame.draw.rect(screen, (150, 200, 255), input_box, 2, border_radius=8)
    
    text_surf = pygame.font.Font(None, 42).render(input_text if input_text else "0", True, WHITE)
    screen.blit(text_surf, text_surf.get_rect(center=input_box.center))
    
    if pygame.time.get_ticks() % 1000 < 500:
        cursor_x = input_box.centerx + text_surf.get_width() // 2 + 5
        pygame.draw.line(screen, WHITE, (cursor_x, input_box.y + 10), (cursor_x, input_box.bottom - 10), 2)
    
    ok_rect = pygame.Rect(x + 80, y + 160, 150, 35)
    ok_color = (50, 200, 50) if input_text.isdigit() and int(input_text) > 0 else (80, 80, 80)
    pygame.draw.rect(screen, ok_color, ok_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, ok_rect, 2, border_radius=5)
    ok_font = pygame.font.Font(None, 28)
    ok_surf = ok_font.render("OK (Enter)", True, WHITE)
    ok_surf_rect = ok_surf.get_rect(center=ok_rect.center)
    screen.blit(ok_surf, ok_surf_rect)
    
    cancel_rect = pygame.Rect(x + 250, y + 160, 150, 35)
    pygame.draw.rect(screen, (200, 50, 50), cancel_rect, border_radius=5)
    pygame.draw.rect(screen, WHITE, cancel_rect, 2, border_radius=5)
    cancel_font = pygame.font.Font(None, 28)
    cancel_surf = cancel_font.render("Cancel (Esc)", True, WHITE)
    cancel_surf_rect = cancel_surf.get_rect(center=cancel_rect.center)
    screen.blit(cancel_surf, cancel_surf_rect)
    
    return {'ok': ok_rect, 'cancel': cancel_rect}

def draw_results():
    global _results_close_rect
    w, h = 520, 320
    x, y = (screen.get_width() - w) // 2, (screen.get_height() - h) // 2
    
    pygame.draw.rect(screen, (30, 30, 30), (x, y, w, h), border_radius=10)
    pygame.draw.rect(screen, (180, 180, 180), (x, y, w, h), 2, border_radius=10)
    
    title = pygame.font.Font(None, 36).render("Simulation Results", True, WHITE)
    screen.blit(title, title.get_rect(center=(x + w // 2, y + 30)))
    
    flow_text = pygame.font.Font(None, 56).render(f"Max Flow: {total_flow}", True, YELLOW)
    screen.blit(flow_text, flow_text.get_rect(center=(x + w // 2, y + 90)))
    
    pygame.draw.line(screen, (100, 100, 100), (x + 16, y + 120), (x + w - 16, y + 120), 2)
    
    font, y_pos = pygame.font.Font(None, 22), y + 136
    entries = augment_history[-10:]
    start_index = max(0, len(augment_history) - len(entries))
    for i, (path_repr, delta) in enumerate(entries):
        col_x = x + 20 if i % 2 == 0 else x + w // 2 + 10
        global_idx = start_index + i + 1
        txt = f"Step {global_idx}: +{delta}  ({len(path_repr)} edges)"
        screen.blit(font.render(txt, True, WHITE), (col_x, y_pos + (i//2) * 26))
    
    ok_rect = pygame.Rect(x + w - 120, y + h - 50, 100, 36)
    pygame.draw.rect(screen, (50, 200, 50), ok_rect, border_radius=6)
    pygame.draw.rect(screen, WHITE, ok_rect, 2, border_radius=6)
    close_surf = font.render("Close", True, WHITE)
    close_rect = close_surf.get_rect(center=ok_rect.center)
    screen.blit(close_surf, close_rect)
    _results_close_rect = ok_rect

# Main loop
running, clock = True, pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if input_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    confirm_edge()
                elif event.key == pygame.K_ESCAPE:
                    cancel_edge()
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit():
                    input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = draw_input_dialog()
                if rects['ok'].collidepoint(event.pos) and input_text.isdigit() and int(input_text) > 0:
                    confirm_edge()
                elif rects['cancel'].collidepoint(event.pos):
                    cancel_edge()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                rects = get_control_rects()
                if rects['play'].collidepoint(event.pos) and not (play_used or simulation_done) and path_exists():
                    playing, play_used = True, True
                elif rects['step'].collidepoint(event.pos):
                    step_requested = True
                elif rects['quit'].collidepoint(event.pos):
                    running = False
                elif rects['reset'].collidepoint(event.pos):
                    reset_simulation()
                elif rects['minus'].collidepoint(event.pos):
                    speed_multiplier = max(0.25, speed_multiplier / 2)
                elif rects['plus'].collidepoint(event.pos):
                    speed_multiplier = min(4.0, speed_multiplier * 2)
                else:
                    node = get_node_at_pos(event.pos)
                    if node:
                        editing_node = moving_node = node
                        selected_edge = None
                    else:
                        selected_edge = get_edge_selected(event.pos)
                        editing_node = None
            
            elif event.button == 3:
                node = get_node_at_pos(event.pos)
                if node:
                    edge_start_node = node
                else:
                    add_node(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3 and edge_start_node:
                end_node = get_node_at_pos(event.pos)
                if end_node and end_node != edge_start_node:
                    add_edge(edge_start_node, end_node)
                edge_start_node = None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and simulation_done:
            if _results_close_rect and _results_close_rect.collidepoint(event.pos):
                simulation_done = False
                augment_history, total_flow = [], 0
        
        if event.type == pygame.KEYDOWN and not input_active:
            if event.key == pygame.K_s and editing_node:
                source_node = editing_node
            elif event.key == pygame.K_k and editing_node:
                sink_node = editing_node
            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                if editing_node:
                    delete_node()
                elif selected_edge:
                    delete_edge()
            editing_node = None
        
        if not input_active:
            update_node_position()
    
    # Simulation
    frame_dt = clock.get_time() / 16.0
    if not input_active:
        if not augmenting and (playing or step_requested):
            path, bottleneck = find_augmenting_path()
            if not path:
                playing, step_requested, simulation_done = False, False, True
                total_flow = sum(e.flow for e in edges if e.node_from == source_node) if source_node else 0
            else:
                current_path, current_bottleneck, augmenting = path, bottleneck, True
                augment_progress = 0.0
                spawn_particles(path, bottleneck)
        
        if augmenting:
            augment_progress += 0.03 * speed_multiplier * frame_dt
            if current_path:
                spawn_particles(current_path, max(1, int(current_bottleneck / 2)))
            
            if augment_progress >= 1.0:
                if current_path:
                    augment_history.append(([(e.node_from.center, e.node_to.center, is_rev) 
                                            for e, is_rev in current_path], current_bottleneck))
                apply_augmentation(current_path, current_bottleneck)
                augmenting, augment_progress, current_path = False, 0.0, None
                if step_requested:
                    playing, step_requested = False, False
    
    draw_scene()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()