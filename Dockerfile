FROM futureys/claude-code-python-development:20260710125000
COPY pyproject.toml /workspace/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
&& uv run csklint install \
 && uv cache clean
COPY . /workspace/
ENTRYPOINT [ "uv", "run" ]
