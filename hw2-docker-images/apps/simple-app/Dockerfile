# first stage to set up the base image with Python
# PYTHONUNBUFFERED to redirect output to the terminal without buffering
FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1 

# builder stage to install dependencies and build the app
FROM base AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY chatroom/ ./chatroom/

# final stage to run the server
FROM base AS final
WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/chatroom/ ./chatroom/

ENV PATH="/opt/venv/bin:$PATH"

USER app
EXPOSE 8080
CMD ["python", "chatroom/server.py"]