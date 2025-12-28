# CodeBook Development Makefile

# Configuration
CICADA_PORT ?= 9999
CODEBOOK_PORT ?= 3000

.PHONY: all dev stop test clean cicada mock

# Start all services
all: dev

# Start dev environment using codebook.yml
dev:
	codebook run

# Start Cicada server only
cicada:
	cicada serve --port $(CICADA_PORT)

# Start mock backend server only
mock:
	python examples/mock_server.py --port $(CODEBOOK_PORT)

# Stop any leftover background services
stop:
	@pkill -f "cicada serve" 2>/dev/null || true
	@pkill -f "mock_server.py" 2>/dev/null || true
	@echo "Stopped background services"

# Run tests
test:
	python -m pytest tests/ -v

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
