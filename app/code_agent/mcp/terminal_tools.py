import subprocess
import time
from typing import Annotated, List

from langsmith import traceable
from mcp.server.fastmcp import FastMCP
from pydantic.fields import Field

mcp = FastMCP()


def run_applescript(script: str) -> tuple[str, str]:
    p = subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()
    return output.decode("utf-8").strip(), error.decode("utf-8").strip()


@traceable(run_type="tool", name="Close Terminal")
@mcp.tool(
    name="close_terminal",
    description="Quit the macOS Terminal application if it is running.",
)
def close_terminal_if_open() -> str:
    try:
        _output, error = run_applescript(
            """
    tell application "System Events"
        if exists process "Terminal" then
            tell application "Terminal" to quit
        end if
    end tell"""
        )
        if error:
            return error
        return "ok"
    except Exception as e:
        return str(e)


@traceable(run_type="tool", name="Open Terminal")
@mcp.tool(
    name="open_terminal",
    description="Activate Terminal.app and optionally focus a window by id. "
    "Returns window/tab info when a new session is ready.",
)
def open_new_terminal(
    window_id: Annotated[
        str,
        Field(
            description="Optional Terminal window id to bring to front; omit or empty for default.",
            default="",
            json_schema_extra={"example": "123456"},
        ),
    ] = "",
) -> str:
    try:
        if window_id:
            _output, error = run_applescript(
                f"""
    tell application "Terminal"
        if (count of windows) > 0 then
            set theWindow to window id {window_id}
            set frontmost to theWindow to true
            activate
        else
            activate
        end if
    end tell"""
            )
        else:
            _output, error = run_applescript(
                """
    tell application "Terminal"
        activate
    end tell"""
            )
        if error:
            return error
        time.sleep(5)
        out, err = _get_all_terminal_window_ids_raw()
        if err:
            return err
        return out or "ok"
    except Exception as e:
        return str(e)

def _get_all_terminal_window_ids_raw() -> tuple[str, str]:
    return run_applescript(
        """
    tell application "Terminal"
        set outputList to {}
        repeat with win in windows
            set windowID to id of win
            set tabCount to number of tabs of win
            repeat with tabIndex from 1 to tabCount
                set end of outputList to {tab tabIndex of window id windowID}
            end repeat
        end repeat
    end tell
    return outputList"""
    )

def get_all_terminal_window_ids() -> str:
    try:
        output, error = _get_all_terminal_window_ids_raw()
        if error:
            return error
        return output or ""
    except Exception as e:
        return str(e)


@traceable(run_type="tool", name="Run Script in Terminal")
@mcp.tool(
    name="run_in_terminal",
    description="Run a shell command string in the front Terminal window via do script.",
)
def run_script_in_terminal(
    script: Annotated[
        str,
        Field(
            description="Shell command or script to run in Terminal.",
            json_schema_extra={"example": "ls -la"},
        ),
    ],
) -> str:
    try:
        escaped = script.replace("\\", "\\\\").replace('"', '\\"')
        output, error = run_applescript(
            f"""
    tell application "Terminal"
        activate
        if (count of windows) > 0 then
            do script "{escaped}" in window 1
        else
            do script "{escaped}"
        end if
    end tell"""
        )
        if error:
            return error
        return output or "ok"
    except Exception as e:
        return str(e)

@traceable(run_type="tool", name="Run Terminal Script Batch")
@mcp.tool(
    name="run_terminal_script",
    description="Run multiple shell commands in ONE terminal session (batch execution)."
)
def run_terminal_script(
    script: Annotated[
        str,
        Field(
            description="Multi-line bash script",
            json_schema_extra={
                "example": "npm install\nnpm run build"
            },
        ),
    ],
) -> str:
    try:
        escaped = script.replace("\\", "\\\\").replace('"', '\\"')

        output, error = run_applescript(f"""
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        do script "{escaped}" in window 1
    else
        do script "{escaped}"
    end if
end tell
""")

        if error:
            return error

        return output or "ok"

    except Exception as e:
        return str(e)


@traceable(run_type="tool", name="Get Terminal Full Text")
@mcp.tool(
    name="get_terminal_full_text",
    description="Read scrollback/history text from the selected tab of the front Terminal window.",
)
def get_terminal_full_text() -> str:
    try:
        output, error = run_applescript(
            """
    tell application "Terminal"
        set fullText to history of selected tab of front window
    end tell"""
        )
        if error:
            return error
        return output or ""
    except Exception as e:
        return str(e)

def _parse_key_code(button):
    button = button.lower()

    keycode_map = {
        'return': 'return',
        'space': 'space',
        'up': 126,
        'down': 125,
        'left': 123,
        'right': 124,
        'a': 0,
        'b': 11,
        'c': 8,
        'd': 2,
        'e': 14,
        'f': 3,
        'g': 5,
        'h': 4,
        'i': 34,
        'j': 38,
        'k': 40,
        'l': 37,
        'm': 46,
        'n': 45,
        'o': 31,
        'p': 35,
        'q': 12,
        'r': 15,
        's': 1,
        't': 17,
        'u': 32,
        'v': 9,
        'w': 13,
        'x': 7,
        'y': 16,
        'z': 6,
        '.': 47,
        'dot': 47,
        '0': 29,
        '1': 18,
        '2': 19,
        '3': 20,
        '4': 21,
        '5': 23,
        '6': 22,
        '7': 26,
        '8': 28,
        '9': 25,
        '-': 27,
    }

    return keycode_map[button]


def _concat_key_codes(key_codes):
    script = ''
    for key in key_codes:
        key_code = _parse_key_code(key)
        script += f'keystroke {key_code}\n'
        script += 'delay 0.5\n'
    return script.strip()

@mcp.tool(name="send_terminal_keyboard_key", description="send a terminal keyboard key to an existing terminal")
def send_terminal_keyboard_key(key_codes: Annotated[
        List[str],
        Field(
            description="send a group of keys in the terminal",
            json_schema_extra={
                "example": ["up", "down"]
            },
        ),
    ]) -> bool:
    print('\nsend_terminal_keyboard_key keycode:', key_codes)
    print('-' * 50)
    script = f'''
    tell application "Terminal"
        activate
        tell application "System Events"
            {_concat_key_codes(key_codes)}
        end tell
    end tell
    '''
    print(script)
    terminal_content, error = run_applescript(script)
    if error:
        return False
    else:
        return True

if __name__ == "__main__":
    mcp.run(transport="stdio")
    # close_terminal_if_open()
    # open_new_terminal()
    # print(get_all_terminal_window_ids())
    # run_script_in_terminal("ls -la")
    # print(get_terminal_full_text())