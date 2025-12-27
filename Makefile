# CodeBook Development Makefile

# Configuration
CICADA_PORT ?= 9999
CODEBOOK_PORT ?= 3000
WATCH_DIR ?= .codebook

.PHONY: all cicada mock watch dev stop test clean

# Start all services
all: dev

# Start Cicada server
cicada:
	cicada serve --port $(CICADA_PORT)

# Start mock backend server
mock:
	python examples/mock_server.py --port $(CODEBOOK_PORT)

# Start codebook watcher
watch:
	codebook -b http://localhost:$(CODEBOOK_PORT) --cicada-url http://localhost:$(CICADA_PORT) \
		watch $(WATCH_DIR) --cicada --exec

# Start all services - Ctrl+C stops everything
dev:
	@trap 'kill 0' EXIT; \
	echo "Starting Cicada on port $(CICADA_PORT)..."; \
	cicada serve --port $(CICADA_PORT) & \
	echo "Starting mock backend on port $(CODEBOOK_PORT)..."; \
	python examples/mock_server.py --port $(CODEBOOK_PORT) & \
	sleep 1; \
	echo "Starting codebook watcher..."; \
	codebook -b http://localhost:$(CODEBOOK_PORT) --cicada-url http://localhost:$(CICADA_PORT) \
		watch $(WATCH_DIR) --cicada --exec

# Stop any leftover background services
stop:
	@pkill -f "cicada serve" 2>/dev/null || true
	@pkill -f "mock_server.py" 2>/dev/null || true
	@echo "Stopped background services"

# Start all services in tmux panes
dev-tmux:
	tmux new-session -d -s codebook 'make cicada' \; \
		split-window -h 'make mock' \; \
		split-window -v 'sleep 2 && make watch' \; \
		attach

# Run tests
test:
	python -m pytest tests/ -v

# Render once (no watch)
render:
	codebook -b http://localhost:$(CODEBOOK_PORT) --cicada-url http://localhost:$(CICADA_PORT) \
		render $(WATCH_DIR) --cicada

# Dry run render
dry-run:
	codebook -b http://localhost:$(CODEBOOK_PORT) --cicada-url http://localhost:$(CICADA_PORT) \
		render $(WATCH_DIR) --cicada --dry-run

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
