import turtle
import math
import random


# Portfolio notes (talk track):
# - I designed the generative art pattern and core turtle-drawing sequence.
# - I expanded it to run multiple patterns at once for continuous screen fill.
# - AI-assisted part: a trig-based bounds check that predicts pattern extents
#   so random start positions stay on-screen.
# - Turtle commands do the visible drawing; trig is only for layout safety math.


screen = turtle.Screen()
screen.bgcolor("black")
screen.tracer(0, 0)

turtle.colormode(255)

colors = [
    (255, 0, 0),
    (0, 200, 255),
    (255, 200, 0),
    (200, 0, 255),
    (0, 255, 150)
]


PADDING = 20
OUTER_REPEATS = 60
INNER_REPEATS = 5
ACTIVE_PATTERNS = 2
STEPS_PER_TICK = 2
TICK_MS = 30
MIN_PATTERN_SPACING = 400
SPAWN_ATTEMPTS = 60
PATTERN_VIEWPORT_FRACTION = 0.55


def calculate_pattern_bounds(scale=1.0):
    x = 0.0
    y = 0.0
    heading = 0.0

    min_x = max_x = x
    min_y = max_y = y

    def move(distance):
        nonlocal x, y, min_x, max_x, min_y, max_y
        radians = math.radians(heading)
        x += math.cos(radians) * distance
        y += math.sin(radians) * distance
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    for _ in range(OUTER_REPEATS):
        for _ in range(INNER_REPEATS):
            heading += 90
            move(50 * scale)
            heading -= 30
            move(40 * scale)
            heading -= 30
            move(50 * scale)
            heading += 42
        move(7 * scale)
        heading += 6

    return min_x, max_x, min_y, max_y


def pick_scale_to_fit():
    min_x, max_x, min_y, max_y = calculate_pattern_bounds(scale=1.0)
    pattern_width = max_x - min_x
    pattern_height = max_y - min_y

    half_width = screen.window_width() / 2 - PADDING
    half_height = screen.window_height() / 2 - PADDING

    if pattern_width <= 0 or pattern_height <= 0:
        return 1.0

    width_scale = (2 * half_width * PATTERN_VIEWPORT_FRACTION) / pattern_width
    height_scale = (2 * half_height * PATTERN_VIEWPORT_FRACTION) / pattern_height
    return max(0.1, min(1.0, width_scale, height_scale))


def random_safe_position(bounds):
    min_x, max_x, min_y, max_y = bounds
    half_width = screen.window_width() / 2 - PADDING
    half_height = screen.window_height() / 2 - PADDING

    x_min = int(-half_width - min_x)
    x_max = int(half_width - max_x)
    y_min = int(-half_height - min_y)
    y_max = int(half_height - max_y)

    if x_min > x_max or y_min > y_max:
        return 0, 0

    return random.randint(x_min, x_max), random.randint(y_min, y_max)


def random_edge_biased_position(bounds, sample_count=12):
    best = random_safe_position(bounds)
    best_score = best[0] * best[0] + best[1] * best[1]

    for _ in range(sample_count - 1):
        candidate = random_safe_position(bounds)
        candidate_score = candidate[0] * candidate[0] + candidate[1] * candidate[1]
        if candidate_score > best_score:
            best = candidate
            best_score = candidate_score

    return best


def random_spaced_position(existing_positions, min_spacing, position_picker, attempts=SPAWN_ATTEMPTS):
    min_distance_sq = min_spacing * min_spacing

    for _ in range(attempts):
        candidate = position_picker()
        if all((candidate[0] - pos[0]) ** 2 + (candidate[1] - pos[1]) ** 2 >= min_distance_sq for pos in existing_positions):
            return candidate

    return position_picker()


class PatternDrawer:
    def __init__(self, scale, start_position):
        self.scale = scale
        self.outer_index = 0
        self.inner_index = 0
        self.done = False
        self.origin = start_position

        self.t = turtle.Turtle()
        self.t.hideturtle()
        self.t.speed(0)
        self.t.width(1)
        self.t.penup()
        self.t.goto(*start_position)
        self.t.pendown()

    def step(self):
        if self.done:
            return

        self.t.color(colors[(self.outer_index // 5) % len(colors)])
        self.t.left(90)
        self.t.forward(50 * self.scale)
        self.t.right(30)
        self.t.forward(40 * self.scale)
        self.t.right(30)
        self.t.forward(50 * self.scale)
        self.t.left(42)

        self.inner_index += 1
        if self.inner_index >= INNER_REPEATS:
            self.inner_index = 0
            self.t.forward(7 * self.scale)
            self.t.left(6)
            self.outer_index += 1

            if self.outer_index >= OUTER_REPEATS:
                self.done = True
                self.t.hideturtle()


scale = pick_scale_to_fit()
bounds = calculate_pattern_bounds(scale)

active_patterns = []
running = True
startup_spawns_remaining = ACTIVE_PATTERNS


def spawn_pattern():
    global startup_spawns_remaining

    existing_positions = [pattern.origin for pattern in active_patterns]
    if startup_spawns_remaining > 0:
        start_position = random_spaced_position(
            existing_positions,
            MIN_PATTERN_SPACING,
            lambda: random_edge_biased_position(bounds),
        )
        startup_spawns_remaining -= 1
    else:
        start_position = random_spaced_position(
            existing_positions,
            MIN_PATTERN_SPACING,
            lambda: random_safe_position(bounds),
        )

    active_patterns.append(PatternDrawer(scale, start_position))


def stop_drawing(x=None, y=None):
    global running
    running = False


def close_program(x=None, y=None):
    stop_drawing()
    screen.ontimer(screen.bye, 1)


def tick():
    if not running:
        return

    while len(active_patterns) < ACTIVE_PATTERNS:
        spawn_pattern()

    finished_patterns = []
    for pattern in active_patterns:
        for _ in range(STEPS_PER_TICK):
            if pattern.done:
                break
            pattern.step()
        if pattern.done:
            finished_patterns.append(pattern)

    for pattern in finished_patterns:
        active_patterns.remove(pattern)

    screen.update()
    screen.ontimer(tick, TICK_MS)


screen.listen()
screen.onkey(stop_drawing, "space")
screen.onkey(close_program, "Escape")
screen.onkey(close_program, "q")
screen.onclick(close_program)

tick()
        
        
turtle.done()
    
