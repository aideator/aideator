In practice you have two reliable “end-of-stream” signals:

1. EOF on stdout (the pipe closes when the `claude` process exits)
2. The explicit “finished” event that the Anthropic stream sends  
   (JSON has `stop_reason` or `[DONE]` if you’re reading raw SSE)

Either works. The simplest pattern in Python is to iterate over stdout;
the loop stops on EOF, so the next line in your code is the callback.

```python
import json
import subprocess
from pathlib import Path

def handle_chunk(chunk: dict) -> None:
    # whatever you already do with each JSON message
    print(chunk["text"], end="", flush=True)

def on_finished() -> None:
    print("\n<callback fired – generation complete>")

# Path to the `claude` CLI wrapper or any other executable
CMD = ["claude", "--model", "opus", "--stream=true"]

with subprocess.Popen(
    CMD,
    stdout=subprocess.PIPE,   # get a pipe we can iterate over
    stderr=subprocess.PIPE,
    text=True,                # str instead of bytes
    bufsize=1,                # line-buffered
) as proc:
    try:
        for line in proc.stdout:          # stops automatically on EOF
            if not line.strip():          # skip blanks if any
                continue
            if line.strip() == "[DONE]":  # raw SSE sentinel – optional
                break
            chunk = json.loads(line)
            handle_chunk(chunk)
    finally:
        proc.wait()  # make sure the child is reaped
        on_finished()
```

Key points:

- `for line in proc.stdout` keeps yielding until the pipe is closed, so the
  loop ends when Claude is finished even if you don’t get an explicit
  `[DONE]`.
- If you do get a special “finished” event (`stop_reason`, `[DONE]`, etc.),
  you can break out of the loop earlier as shown.
- The callback (`on_finished`) is invoked exactly once, after the loop, so
  you won’t miss the end even if Claude exits abnormally.

If you’re using Anthropic’s official Python SDK instead of an external
process, the pattern is the same—iterate over the generator and call your
callback when the `for` loop completes:

```python
from anthropic import Anthropic

client = Anthropic()
stream = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    stream=True,
    messages=[{"role": "user", "content": "Hello"}],
)

for chunk in stream:  # yields until the final chunk
    handle_chunk(chunk)

on_finished()
```

No extra threads, no polling—just treat the end of iteration as the cue to fire your callback.