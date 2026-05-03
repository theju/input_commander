import time
from bottle import Bottle, request, run, response
from evdev import UInput, AbsInfo, ecodes as ec

MOUSE_CAPABILITIES = {
    ec.EV_KEY: [ec.BTN_LEFT, ec.BTN_RIGHT],
    ec.EV_ABS: [
        (ec.ABS_X, AbsInfo(0, 0, 1920, 0, 0, 0)),
        (ec.ABS_Y, AbsInfo(0, 0, 1080, 0, 0, 0)),
    ],
    ec.EV_REL: [ec.REL_WHEEL, ec.REL_HWHEEL],
}

MOUSE_BUTTONS = {
    "left": ec.BTN_LEFT,
    "right": ec.BTN_RIGHT,
}

KEYBOARD_CAPABILITIES = {
    ec.EV_KEY: sorted(
        code
        for name, code in ec.ecodes.items()
        if name.startswith("KEY_") and isinstance(code, int) and 0 < code < ec.KEY_MAX
    ),
}

KEY_ALIASES = {
    "CTRL": "LEFTCTRL",
    "CONTROL": "LEFTCTRL",
    "SHIFT": "LEFTSHIFT",
    "ALT": "LEFTALT",
    "OPTION": "LEFTALT",
    "CMD": "LEFTMETA",
    "COMMAND": "LEFTMETA",
    "WIN": "LEFTMETA",
    "WINDOWS": "LEFTMETA",
    "SUPER": "LEFTMETA",
    "ESC": "ESC",
    "RETURN": "ENTER",
    "DEL": "DELETE",
    "BKSP": "BACKSPACE",
    "PGUP": "PAGEUP",
    "PAGE_UP": "PAGEUP",
    "PGDN": "PAGEDOWN",
    "PAGE_DOWN": "PAGEDOWN",
    "SPACEBAR": "SPACE",
}

SPECIAL_CHAR_MAP = {
    " ": ("SPACE", False),
    "\n": ("ENTER", False),
    "\t": ("TAB", False),
    "-": ("MINUS", False),
    "_": ("MINUS", True),
    "=": ("EQUAL", False),
    "+": ("EQUAL", True),
    "[": ("LEFTBRACE", False),
    "{": ("LEFTBRACE", True),
    "]": ("RIGHTBRACE", False),
    "}": ("RIGHTBRACE", True),
    "\\": ("BACKSLASH", False),
    "|": ("BACKSLASH", True),
    ";": ("SEMICOLON", False),
    ":": ("SEMICOLON", True),
    "'": ("APOSTROPHE", False),
    "\"": ("APOSTROPHE", True),
    ",": ("COMMA", False),
    "<": ("COMMA", True),
    ".": ("DOT", False),
    ">": ("DOT", True),
    "/": ("SLASH", False),
    "?": ("SLASH", True),
    "`": ("GRAVE", False),
    "~": ("GRAVE", True),
    "!": ("1", True),
    "@": ("2", True),
    "#": ("3", True),
    "$": ("4", True),
    "%": ("5", True),
    "^": ("6", True),
    "&": ("7", True),
    "*": ("8", True),
    "(": ("9", True),
    ")": ("0", True),
}

def _clamp_abs(value):
    try:
        vv = int(value)
    except (TypeError, ValueError):
        vv = 0
    return vv

def _require_int(value, name):
    if value is None:
        raise ValueError(f"{name} must be provided.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc

def _normalize_mouse_button(button):
    if button is None:
        return ec.BTN_LEFT

    if isinstance(button, str):
        normalized = button.strip().lower()
        if normalized in MOUSE_BUTTONS:
            return MOUSE_BUTTONS[normalized]

    raise ValueError('button must be "left" or "right".')

mouse = UInput(MOUSE_CAPABILITIES, name="duckai-virtual-mouse")
keyboard = UInput(KEYBOARD_CAPABILITIES, name="duckai-virtual-keyboard")

def move_mouse(x, y):
    mouse.write(ec.EV_ABS, ec.ABS_X, _clamp_abs(x))
    mouse.write(ec.EV_ABS, ec.ABS_Y, _clamp_abs(y))
    mouse.syn()

def mouse_button_down(button=None):
    mouse.write(ec.EV_KEY, _normalize_mouse_button(button), 1)
    mouse.syn()

def mouse_button_up(button=None):
    mouse.write(ec.EV_KEY, _normalize_mouse_button(button), 0)
    mouse.syn()

def click_mouse(button=None):
    mouse_button_down(button)
    time.sleep(0.05)
    mouse_button_up(button)

def drag_mouse(x, y, to_x, to_y, button=None, duration=0.25, steps=20):
    start_x = _require_int(x, "x")
    start_y = _require_int(y, "y")
    end_x = _require_int(to_x, "to_x")
    end_y = _require_int(to_y, "to_y")
    button_code = _normalize_mouse_button(button)

    try:
        duration = float(duration)
    except (TypeError, ValueError) as exc:
        raise ValueError("duration must be a number.") from exc

    steps = _require_int(steps, "steps")
    if duration < 0:
        raise ValueError("duration must be zero or greater.")
    if steps < 1:
        raise ValueError("steps must be at least 1.")

    move_mouse(start_x, start_y)
    time.sleep(0.05)
    mouse.write(ec.EV_KEY, button_code, 1)
    mouse.syn()

    try:
        step_delay = duration / steps if duration else 0
        for step in range(1, steps + 1):
            progress = step / steps
            next_x = round(start_x + (end_x - start_x) * progress)
            next_y = round(start_y + (end_y - start_y) * progress)
            move_mouse(next_x, next_y)
            if step_delay:
                time.sleep(step_delay)
    finally:
        mouse.write(ec.EV_KEY, button_code, 0)
        mouse.syn()

def scroll_mouse(x, y):
    if y:
        mouse.write(ec.EV_REL, ec.REL_WHEEL, y)
    if x:
        mouse.write(ec.EV_REL, ec.REL_HWHEEL, x)
    mouse.syn()

def _normalize_key_name(key):
    if isinstance(key, int):
        return key
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string or integer key code.")

    normalized = key.strip().upper().replace("-", "_").replace(" ", "_")
    normalized = KEY_ALIASES.get(normalized, normalized)
    if not normalized.startswith("KEY_"):
        normalized = f"KEY_{normalized}"

    key_code = ec.ecodes.get(normalized)
    if not isinstance(key_code, int):
        raise ValueError(f"Unsupported key: {key}")
    return key_code

def key_down(key):
    keyboard.write(ec.EV_KEY, _normalize_key_name(key), 1)
    keyboard.syn()

def key_up(key):
    keyboard.write(ec.EV_KEY, _normalize_key_name(key), 0)
    keyboard.syn()

def tap_key(key):
    key_code = _normalize_key_name(key)
    keyboard.write(ec.EV_KEY, key_code, 1)
    keyboard.syn()
    time.sleep(0.03)
    keyboard.write(ec.EV_KEY, key_code, 0)
    keyboard.syn()

def press_combo(keys):
    if not isinstance(keys, list) or not keys:
        raise ValueError("keys must be a non-empty list.")

    normalized_keys = [_normalize_key_name(key) for key in keys]
    for key_code in normalized_keys:
        keyboard.write(ec.EV_KEY, key_code, 1)
        keyboard.syn()

    time.sleep(0.03)

    for key_code in reversed(normalized_keys):
        keyboard.write(ec.EV_KEY, key_code, 0)
        keyboard.syn()

def _char_to_key_press(char):
    if "a" <= char <= "z":
        return (char.upper(), False)
    if "A" <= char <= "Z":
        return (char, True)
    if "0" <= char <= "9":
        return (char, False)
    if char in SPECIAL_CHAR_MAP:
        return SPECIAL_CHAR_MAP[char]
    raise ValueError(f"Unsupported character for typing: {char!r}")

def type_text(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string.")

    for char in text:
        key_name, needs_shift = _char_to_key_press(char)
        if needs_shift:
            key_down("LEFTSHIFT")
        tap_key(key_name)
        if needs_shift:
            key_up("LEFTSHIFT")

def enable_cors(func):
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.status = 204
            return

        return func(*args, **kwargs)
    return wrapper

app = Bottle()

@app.route('/mouse', method=['OPTIONS', 'POST'])
@enable_cors
def handle_mouse():
    data = request.json or {}
    action = data.get('action')
    x = data.get('x')
    y = data.get('y')
    button = data.get('button')

    if action not in ['click', 'down', 'up', 'drop', 'move', 'scroll', 'drag']:
        response.status = 400
        return {'error': 'Invalid action. Use "click", "down", "up", "drop", "move", "scroll", or "drag".'}

    try:
        if action == 'move':
            if x is None or y is None:
                response.status = 400
                return {'error': 'x and y must be provided for move.'}
            move_mouse(x, y)
            return {'status': 'Mouse moved', 'x': x, 'y': y}

        if action == 'click':
            click_mouse(button)
            return {'status': 'Mouse clicked', 'button': button or 'left'}

        if action == 'down':
            mouse_button_down(button)
            return {'status': 'Mouse button pressed', 'button': button or 'left'}

        if action in ['up', 'drop']:
            mouse_button_up(button)
            return {'status': 'Mouse button released', 'button': button or 'left'}

        if action == 'scroll':
            scroll_mouse(x, y)
            return {'status': 'Mouse scrolled'}

        drag_mouse(
            x,
            y,
            data.get('to_x'),
            data.get('to_y'),
            button=button,
            duration=data.get('duration', 0.25),
            steps=data.get('steps', 20),
        )
        return {
            'status': 'Mouse dragged',
            'button': button or 'left',
            'x': x,
            'y': y,
            'to_x': data.get('to_x'),
            'to_y': data.get('to_y'),
        }
    except ValueError as exc:
        response.status = 400
        return {'error': str(exc)}

@app.route('/keyboard', method=['OPTIONS', 'POST'])
@enable_cors
def handle_keyboard():
    data = request.json or {}
    action = data.get('action')
    key = data.get('key')
    keys = data.get('keys')
    text = data.get('text')

    if action not in ['tap', 'down', 'up', 'combo', 'type']:
        response.status = 400
        return {'error': 'Invalid action. Use "tap", "down", "up", "combo", or "type".'}

    try:
        if action == 'tap':
            if key is None:
                response.status = 400
                return {'error': 'key must be provided for tap.'}
            tap_key(key)
            return {'status': 'Key tapped', 'key': key}

        if action == 'down':
            if key is None:
                response.status = 400
                return {'error': 'key must be provided for down.'}
            key_down(key)
            return {'status': 'Key pressed', 'key': key}

        if action == 'up':
            if key is None:
                response.status = 400
                return {'error': 'key must be provided for up.'}
            key_up(key)
            return {'status': 'Key released', 'key': key}

        if action == 'combo':
            press_combo(keys)
            return {'status': 'Key combo sent', 'keys': keys}

        if text is None:
            response.status = 400
            return {'error': 'text must be provided for type.'}
        type_text(text)
        return {'status': 'Text typed', 'text': text}
    except ValueError as exc:
        response.status = 400
        return {'error': str(exc)}

if __name__ == "__main__":
    run(app, host='localhost', port=8080)
