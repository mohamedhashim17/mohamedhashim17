import math
import random
from collections import deque

COLS = 53
ROWS = 7
CELL_SIZE = 12
GAP = 3
PADDING = 8

BG_COLOR = "#0d1117"
CELL_COLOR = "#161b22"
SNAKE_HEAD = "#c026d3"
SNAKE_BODY = [
    "#a21caf",
    "#9333ea",
    "#7e22ce",
    "#6b21a8",
]
FOOD_SHADES = [
    "#14532d",
    "#15803d",
    "#16a34a",
    "#22c55e",
    "#4ade80",
    "#86efac",
]

FOOD_COUNT = 135
MAX_STEPS = 220
STEP_DURATION = 0.14
INITIAL_LENGTH = 5
MAX_LENGTH = 5


def get_neighbors(pos):
    x, y = pos
    neighbors = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            neighbors.append((nx, ny))
    return neighbors


def bfs_next_move(head, target, body_set):
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

    for nxt in get_neighbors(head):
        if nxt not in body_set:
            return nxt
    return None


def pick_reference_cell(occupied):
    empty = [
        (x, y)
        for x in range(COLS)
        for y in range(ROWS)
        if (x, y) not in occupied
    ]
    if not empty:
        return None

    weights = []
    for x, y in empty:
        # Dense cluster across center-right (around col 12..44) with lighter edges
        center_dist = abs(x - 27) / 27.0
        row_factor = 1.0 - (abs(y - 3) / 4.0) * 0.35
        w = max(0.12, (1.15 - center_dist * 0.85) * row_factor)
        weights.append(w)

    pos = random.choices(empty, weights=weights, k=1)[0]
    color = random.choice(FOOD_SHADES)
    return {"pos": pos, "color": color}


def seed_initial_foods(snake_set):
    foods = []
    occupied = set(snake_set)
    while len(foods) < FOOD_COUNT:
        item = pick_reference_cell(occupied)
        if not item:
            break
        foods.append(item)
        occupied.add(item["pos"])
    return foods


def nearest_food(head, foods):
    if not foods:
        return None
    return min(foods, key=lambda f: math.dist(head, f["pos"]))


def simulate_game():
    random.seed()
    start_x = COLS - 2
    start_y = 0
    snake = [(start_x - i, start_y) for i in range(INITIAL_LENGTH)]
    foods = seed_initial_foods(set(snake))

    frames = []

    for _ in range(MAX_STEPS):
        frames.append({
            "snake": list(snake),
            "foods": [{"pos": f["pos"], "color": f["color"]} for f in foods],
        })

        target = nearest_food(snake[0], foods)
        target_pos = target["pos"] if target else None

        obstacles = set(snake[:-1])
        next_pos = bfs_next_move(snake[0], target_pos, obstacles) if target_pos else None

        if next_pos is None:
            snake = [(start_x - i, start_y) for i in range(INITIAL_LENGTH)]
            foods = seed_initial_foods(set(snake))
            continue

        snake.insert(0, next_pos)

        eaten_idx = next((idx for idx, f in enumerate(foods) if f["pos"] == next_pos), None)
        if eaten_idx is not None:
            foods.pop(eaten_idx)
            occupied = set(snake) | {f["pos"] for f in foods}
            replacement = pick_reference_cell(occupied)
            if replacement:
                foods.append(replacement)

        snake.pop()

        while len(foods) < FOOD_COUNT:
            occupied = set(snake) | {f["pos"] for f in foods}
            extra = pick_reference_cell(occupied)
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

    for f_idx in range(FOOD_COUNT):
        kf = [f"@keyframes food{f_idx}Move {{"]
        for i, f in enumerate(frames):
            pct = (i / n) * 100
            if f_idx < len(f["foods"]):
                fx, fy = f["foods"][f_idx]["pos"]
                fcolor = f["foods"][f_idx]["color"]
                px, py = cell_xy(fx, fy)
                kf.append(
                    f"  {pct:.2f}% {{ transform: translate({px}px, {py}px); fill: {fcolor}; opacity: 1; }}"
                )
            else:
                kf.append(f"  {pct:.2f}% {{ opacity: 0; }}")
        kf.append("}")
        svg.extend(kf)
        svg.append(
            f"  #food-{f_idx} {{ animation: food{f_idx}Move {total_duration}s steps(1, end) infinite; }}"
        )

    for seg_idx in range(MAX_LENGTH):
        kf = [f"@keyframes seg{seg_idx}Move {{"]
        for i, f in enumerate(frames):
            pct = (i / n) * 100
            snake = f["snake"]
            if seg_idx < len(snake):
                sx, sy = snake[seg_idx]
                px, py = cell_xy(sx, sy)
                kf.append(
                    f"  {pct:.2f}% {{ transform: translate({px}px, {py}px); opacity: 1; }}"
                )
            else:
                kf.append(f"  {pct:.2f}% {{ opacity: 0; }}")
        kf.append("}")
        svg.extend(kf)
        svg.append(
            f"  #seg-{seg_idx} {{ animation: seg{seg_idx}Move {total_duration}s steps(1, end) infinite; }}"
        )

    svg.append("</style>")
    svg.append(
        f'<rect width="{width}" height="{height}" rx="8" ry="8" fill="{BG_COLOR}" />'
    )

    svg.append('<g id="grid">')
    for x in range(COLS):
        for y in range(ROWS):
            px, py = cell_xy(x, y)
            svg.append(
                f'  <rect class="grid-cell" x="{px}" y="{py}" width="{CELL_SIZE}" height="{CELL_SIZE}" />'
            )
    svg.append("</g>")

    svg.append('<g id="foods">')
    for f_idx in range(FOOD_COUNT):
        svg.append(
            f'  <rect id="food-{f_idx}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" ry="2.5" />'
        )
    svg.append("</g>")

    svg.append('<g id="snake">')
    for seg_idx in range(MAX_LENGTH - 1, -1, -1):
        fill = SNAKE_HEAD if seg_idx == 0 else SNAKE_BODY[min(seg_idx - 1, len(SNAKE_BODY) - 1)]
        svg.append(
            f'  <rect id="seg-{seg_idx}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" ry="2.5" fill="{fill}" />'
        )
    svg.append("</g>")
    svg.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(svg))
    print(f"Generated {output_path} ({width}x{height}px, {n} frames)")


if __name__ == "__main__":
    game_frames = simulate_game()
    generate_svg(game_frames, "snake-game.svg")
