# input-commander

Simple Bottle server that exposes virtual mouse and keyboard input via `evdev`.

## Instructions

1. Add the `input` group to the current user.
2. Run the `scripts/uinput.sh` before starting the server below.

## Endpoints

### `POST /mouse`

Supported actions:

- `{"action": "move", "x": 960, "y": 540}`
- `{"action": "click"}`
- `{"action": "down"}`
- `{"action": "up"}`
- `{"action": "drop"}`
- `{"action": "scroll", "x": 0, "y": -1}`
- `{"action": "drag", "x": 200, "y": 200, "to_x": 800, "to_y": 600}`

Mouse `click`, `down`, `up`, `drop`, and `drag` default to the left button. Use `"button": "right"` for right-button actions.

`drag` moves to `x`/`y`, presses the mouse button, moves to `to_x`/`to_y`, and releases the button. Optional `duration` and `steps` fields control the drag speed and interpolation.

### `POST /keyboard`

Supported actions:

- `{"action": "tap", "key": "enter"}`
- `{"action": "down", "key": "ctrl"}`
- `{"action": "up", "key": "ctrl"}`
- `{"action": "combo", "keys": ["ctrl", "alt", "t"]}`
- `{"action": "type", "text": "Hello, world!"}`

Key names accept either Linux input names such as `KEY_ENTER` or short forms such as `enter`, `leftshift`, and `page_down`.

`type` currently supports letters, digits, whitespace, and common US keyboard punctuation.
