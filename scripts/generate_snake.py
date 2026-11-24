import math
import random
from collections import deque

# --- Grid & Visual Configuration ---
COLS = 53
ROWS = 11
CELL_SIZE = 12
GAP = 3
PADDING = 10

BG_COLOR = "#0d1117"       # Dark background
CELL_COLOR = "#161b22"     # Empty grid cell color
SNAKE_HEAD = "#a855f7"     # Vibrant Purple Head
SNAKE_BODY = [
    "#9333ea",
    "#7e22ce",
    "#6b21a8",
    "#581c87",
]
FOOD_SHADES = [
    "#2ea043",             # Classic Green
    "#3fb950",             # Bright Green
    "#238636",             # Deep Green
    "#196c2e",             # Dark Green
    "#56d364",             # Light Green
]

FOOD_COUNT = 8             # Number of green boxes present on the grid at once
MAX_STEPS = 240            # Total simulation steps in loop
STEP_DURATION = 0.12       # Seconds per step
INITIAL_LENGTH = 4
MAX_LENGTH = 20


def get_neighbors(pos):
    x, y = pos
    neighbors = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            neighbors.append((nx, ny))
    return neighbors


def bfs_next_move(head, target, body_set):
    """Finds the shortest safe path from head to target."""
    queue = deque([(head, [])])
    visited = {head}

    while queue:
        curr, path = queue.popleft()
        if curr == target and path:
            return path[0]

        neighbors = get_neighbors(curr)
        random.shuffle(neighbors)
        for nxt in neighbors:
            if nxt not in visited and nxt not in body_set:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))

    # Fallback: pick any safe adjacent cell
    for nxt in get_neighbors(head):
        if nxt not in body_set:
            return nxt
    return None


def spawn_single_food(occupied):
    empty = [
        (x, y)
        for x in range(COLS)
        for y in range(ROWS)
        if (x, y) not in occupied
    ]
    if not empty:
        return None
    pos = random.choice(empty)
    color = random.choice(FOOD_SHADES)
    return {"pos": pos, "color": color}


def choose_target_food(head, foods):
    """Picks the closest green box to the snake's head."""
    if not foods:
        return None
    return min(
        foods,
        key=lambda f: math.dist(head, f["pos"]),
    )


def simulate_game():
    random.seed()
    start_y = ROWS // 2
    snake = [(COLS // 2 - i, start_y) for i in range(INITIAL_LENGTH)]

    foods = []
    occupied = set(snake)
    for _ in range(FOOD_COUNT):
        item = spawn_single_food(occupied)
        if item:
            foods.append(item)
            occupied.add(item["pos"])

    frames = []

    for _ in range(MAX_STEPS):
        # Snapshot current snake & all active green boxes
        frames.append({
            "snake": list(snake),
            "foods": [{"pos": f["pos"], "color": f["color"]} for f in foods],
        })

        target_item = choose_target_food(snake[0], foods)
        target_pos = target_item["pos"] if target_item else None

        obstacles = set(snake[:-1])
        next_pos = bfs_next_move(snake[0], target_pos, obstacles) if target_pos else None

        if next_pos is None:
            # Reset snake position while keeping multiple green boxes active
            snake = [(COLS // 2 - i, start_y) for i in range(INITIAL_LENGTH)]
            foods = []
            occupied = set(snake)
            for _ in range(FOOD_COUNT):
                item = spawn_single_food(occupied)
                if item:
                    foods.append(item)
                    occupied.add(item["pos"])
            continue

        snake.insert(0, next_pos)

        eaten_index = next((idx for idx, f in enumerate(foods) if f["pos"] == next_pos), None)
        if eaten_index is not None:
            # Eat that green box, grow (up to MAX_LENGTH), and spawn a replacement
            foods.pop(eaten_index)
            if len(snake) > MAX_LENGTH:
                snake.pop()
            occupied = set(snake) | {f["pos"] for f in foods}
            replacement = spawn_single_food(occupied)
            if replacement:
                foods.append(replacement)
        else:
            snake.pop()

        # Always keep FOOD_COUNT green boxes on the board if space allows
        while len(foods) < FOOD_COUNT:
            occupied = set(snake) | {f["pos"] for f in foods}
            extra = spawn_single_food(occupied)
            if extra:
                foods.append(extra)
            else:
                break

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
        f"  .grid-cell {{ fill: {CELL_COLOR}; rx: 2.5px; ry: 2.5px; }}",
    ]

    # 1. CSS Keyframes for each of the FOOD_COUNT green boxes
    for f_idx in range(FOOD_COUNT):
        food_kf = [f"@keyframes food{f_idx}Move {{"]
        for i, f in enumerate(frames):
            pct = (i / n) * 100
            if f_idx < len(f["foods"]):
                fx, fy = f["foods"][f_idx]["pos"]
                fcolor = f["foods"][f_idx]["color"]
                px, py = cell_xy(fx, fy)
                food_kf.append(
                    f"  {pct:.2f}% {{ transform: translate({px}px, {py}px); fill: {fcolor}; opacity: 1; }}"
                )
            else:
                food_kf.append(f"  {pct:.2f}% {{ opacity: 0; }}")
        food_kf.append("}")
        svg.extend(food_kf)
        svg.append(
            f"  #food-{f_idx} {{ animation: food{f_idx}Move {total_duration}s steps(1, end) infinite; }}"
        )

    # 2. CSS Keyframes for each snake segment
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
        f'<rect width="{width}" height="{height}" rx="8" ry="8" fill="{BG_COLOR}" />'
    )

    # 4. Grid Cells
    svg.append('<g id="grid">')
    for x in range(COLS):
        for y in range(ROWS):
            px, py = cell_xy(x, y)
            svg.append(
                f'  <rect class="grid-cell" x="{px}" y="{py}" width="{CELL_SIZE}" height="{CELL_SIZE}" />'
            )
    svg.append("</g>")

    # 5. Multiple Green Boxes (Food)
    svg.append('<g id="foods">')
    for f_idx in range(FOOD_COUNT):
        svg.append(
            f'  <rect id="food-{f_idx}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" ry="2.5" />'
        )
    svg.append("</g>")

    # 6. Purple Snake Segments (back-to-front so head renders on top)
    svg.append('<g id="snake">')
    for seg_idx in range(MAX_LENGTH - 1, -1, -1):
        if seg_idx == 0:
            svg.append('  <g id="seg-0">')
            svg.append(
                f'    <rect width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" ry="3" fill="{SNAKE_HEAD}" />'
            )
            svg.append(
                f'    <circle cx="4" cy="4" r="1.2" fill="#ffffff" />'
            )
            svg.append(
                f'    <circle cx="8" cy="4" r="1.2" fill="#ffffff" />'
            )
            svg.append("  </g>")
        else:
            color = SNAKE_BODY[min((seg_idx - 1) // 4, len(SNAKE_BODY) - 1)]
            svg.append(
                f'  <rect id="seg-{seg_idx}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" ry="2.5" fill="{color}" />'
            )
    svg.append("</g>")
    svg.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(svg))
    print(f"Generated {output_path} ({width}x{height}px, {n} frames, {FOOD_COUNT} green boxes)")


if __name__ == "__main__":
    game_frames = simulate_game()
    generate_svg(game_frames, "snake-game.svg")
