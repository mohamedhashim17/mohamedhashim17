import random
from collections import deque

# --- Grid & Visual Configuration ---
COLS = 53
ROWS = 7
CELL_SIZE = 14
GAP = 3
PADDING = 10

BG_COLOR = "#0d1117"       # GitHub Dark Dimmed/Default background
CELL_COLOR = "#161b22"     # Empty grid cell color
SNAKE_HEAD = "#a855f7"     # Vibrant Purple Head
SNAKE_BODY = [
    "#9333ea",
    "#7e22ce",
    "#6b21a8",
    "#581c87",
]
FOOD_SHADES = [
    "#39d353",             # Bright Neon Green
    "#26a641",             # Medium Green
    "#006d32",             # Deep Forest Green
    "#4ade80",             # Mint Green
]

MAX_STEPS = 220            # Total frames in the loop
STEP_DURATION = 0.14       # Seconds per move (lower = faster)
INITIAL_LENGTH = 4
MAX_LENGTH = 18


def get_neighbors(pos):
    x, y = pos
    neighbors = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            neighbors.append((nx, ny))
    return neighbors


def bfs_next_move(head, target, body_set):
    """Finds the shortest safe path to the food."""
    queue = deque([(head, [])])
    visited = {head}

    while queue:
        curr, path = queue.popleft()
        if curr == target and path:
            return path[0]

        neighbors = get_neighbors(curr)
        random.shuffle(neighbors)  # Adds organic movement variety
        for nxt in neighbors:
            if nxt not in visited and nxt not in body_set:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))

    # Fallback: pick any safe adjacent cell if food is temporarily blocked
    for nxt in get_neighbors(head):
        if nxt not in body_set:
            return nxt
    return None


def spawn_food(occupied):
    empty = [
        (x, y)
        for x in range(COLS)
        for y in range(ROWS)
        if (x, y) not in occupied
    ]
    if not empty:
        return None
    return random.choice(empty), random.choice(FOOD_SHADES)


def simulate_game():
    random.seed()  # Fresh random game on every GitHub Action run
    start_y = ROWS // 2
    snake = [(INITIAL_LENGTH - 1 - i, start_y) for i in range(INITIAL_LENGTH)]
    food_pos, food_color = spawn_food(set(snake))

    frames = []

    for _ in range(MAX_STEPS):
        frames.append({
            "snake": list(snake),
            "food": (food_pos, food_color),
        })

        # Exclude tail tip from obstacles since it will vacate on next step
        obstacles = set(snake[:-1])
        next_pos = bfs_next_move(snake[0], food_pos, obstacles)

        # Reset smoothly if boxed in
        if next_pos is None:
            snake = [(INITIAL_LENGTH - 1 - i, start_y) for i in range(INITIAL_LENGTH)]
            food_pos, food_color = spawn_food(set(snake))
            continue

        snake.insert(0, next_pos)

        if next_pos == food_pos:
            if len(snake) > MAX_LENGTH:
                snake.pop()
            spawned = spawn_food(set(snake))
            if spawned:
                food_pos, food_color = spawned
        else:
            snake.pop()

    return frames


def generate_svg(frames, output_path="snake-game.svg"):
    width = PADDING * 2 + COLS * CELL_SIZE + (COLS - 1) * GAP
    height = PADDING * 2 + ROWS * CELL_SIZE + (ROWS - 1) * GAP
    total_duration = round(len(frames) * STEP_DURATION, 2)
    n = len(frames)

    def cell_xy(cx, cy):
        return (
            PADDING + cx * (CELL_SIZE + GAP),
            PADDING + cy * (CELL_SIZE + GAP),
        )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Animated Snake Game">',
        "<style>",
        f"  .grid-cell {{ fill: {CELL_COLOR}; rx: 3px; ry: 3px; }}",
    ]

    # 1. Build CSS Keyframes for Food
    food_kf = ["@keyframes foodMove {"]
    for i, f in enumerate(frames):
        pct = (i / n) * 100
        (fx, fy), fcolor = f["food"]
        px, py = cell_xy(fx, fy)
        food_kf.append(
            f"  {pct:.2f}% {{ transform: translate({px}px, {py}px); fill: {fcolor}; }}"
        )
    food_kf.append("}")
    svg.extend(food_kf)
    svg.append(
        f"  #food {{ animation: foodMove {total_duration}s steps(1, end) infinite; }}"
    )

    # 2. Build CSS Keyframes for Each Snake Segment
    for seg_idx in range(MAX_LENGTH):
        seg_kf = [f"@keyframes seg{seg_idx}Move {{"]
        for i, f in enumerate(frames):
            pct = (i / n) * 100
            snake = f["snake"]
            if seg_idx < len(snake):
                sx, sy = snake[seg_idx]
                px, py = cell_xy(sx, sy)
                seg_kf.append(
                    f"  {pct:.2f}% {{ transform: translate({px}px, {py}px); opacity: 1; }}"
                )
            else:
                seg_kf.append(f"  {pct:.2f}% {{ opacity: 0; }}")
        seg_kf.append("}")
        svg.extend(seg_kf)
        svg.append(
            f"  #seg-{seg_idx} {{ animation: seg{seg_idx}Move {total_duration}s steps(1, end) infinite; }}"
        )

    svg.append("</style>")

    # 3. Background Canvas
    svg.append(
        f'<rect width="{width}" height="{height}" rx="10" ry="10" fill="{BG_COLOR}" />'
    )

    # 4. Static Grid Background
    svg.append('<g id="grid">')
    for x in range(COLS):
        for y in range(ROWS):
            px, py = cell_xy(x, y)
            svg.append(
                f'  <rect class="grid-cell" x="{px}" y="{py}" width="{CELL_SIZE}" height="{CELL_SIZE}" />'
            )
    svg.append("</g>")

    # 5. Animated Green Food Dot
    svg.append(
        f'<circle id="food" cx="{CELL_SIZE / 2}" cy="{CELL_SIZE / 2}" r="{CELL_SIZE * 0.38:.1f}" />'
    )

    # 6. Animated Purple Snake Segments (Rendered back-to-front so head overlaps cleanly)
    svg.append('<g id="snake">')
    for seg_idx in range(MAX_LENGTH - 1, -1, -1):
        if seg_idx == 0:
            # Distinct Snake Head with Eyes
            svg.append(f'  <g id="seg-0">')
            svg.append(
                f'    <rect width="{CELL_SIZE}" height="{CELL_SIZE}" rx="4" ry="4" fill="{SNAKE_HEAD}" />'
            )
            svg.append(
                f'    <circle cx="4.5" cy="4.5" r="1.4" fill="#ffffff" />'
            )
            svg.append(
                f'    <circle cx="9.5" cy="4.5" r="1.4" fill="#ffffff" />'
            )
            svg.append("  </g>")
        else:
            color = SNAKE_BODY[min((seg_idx - 1) // 3, len(SNAKE_BODY) - 1)]
            inset = 0.5 if seg_idx > MAX_LENGTH - 4 else 0
            size = CELL_SIZE - inset * 2
            svg.append(
                f'  <rect id="seg-{seg_idx}" x="{inset}" y="{inset}" width="{size}" height="{size}" rx="3.5" ry="3.5" fill="{color}" />'
            )
    svg.append("</g>")
    svg.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(svg))
    print(f"Generated {output_path} ({width}x{height}px, {n} frames)")


if __name__ == "__main__":
    game_frames = simulate_game()
    generate_svg(game_frames, "snake-game.svg")
