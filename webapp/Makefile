.PHONY: help dev start stop mongodb-start mongodb-stop mongodb-status install clean seed

help:
	@echo "Available commands:"
	@echo "  make dev            - Start MongoDB and Next.js development server"
	@echo "  make start          - Alias for 'make dev'"
	@echo "  make stop           - Stop MongoDB and kill dev server"
	@echo "  make mongodb-start  - Start MongoDB service only"
	@echo "  make mongodb-stop   - Stop MongoDB service only"
	@echo "  make mongodb-status - Check MongoDB status"
	@echo "  make install        - Install npm dependencies"
	@echo "  make clean          - Clean node_modules and reinstall"
	@echo "  make seed           - Seed admin account (requires npm run seed-admin)"
	@echo "  make build          - Build for production"
	@echo "  make lint           - Run ESLint"

# Start everything (MongoDB + Next.js dev server)
dev: mongodb-start
	@echo "Starting Next.js development server..."
	@npm run dev

# Alias for dev
start: dev

# Start MongoDB service
mongodb-start:
	@echo "Starting MongoDB..."
	@brew services start mongodb/brew/mongodb-community
	@sleep 2
	@echo "MongoDB started successfully!"

# Stop MongoDB service
mongodb-stop:
	@echo "Stopping MongoDB..."
	@brew services stop mongodb/brew/mongodb-community
	@echo "MongoDB stopped!"

# Check MongoDB status
mongodb-status:
	@brew services list | grep mongodb
	@echo ""
	@mongosh --eval "db.version()" --quiet 2>/dev/null && echo "MongoDB is running" || echo "MongoDB is not running"

# Stop development server and MongoDB
stop:
	@echo "Stopping development server..."
	@-pkill -f "next dev" 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3004 | xargs kill -9 2>/dev/null || true
	@echo "Stopping MongoDB..."
	@brew services stop mongodb/brew/mongodb-community
	@echo "All services stopped!"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@npm install
	@echo "Dependencies installed!"

# Clean and reinstall
clean:
	@echo "Cleaning node_modules..."
	@rm -rf node_modules package-lock.json
	@echo "Reinstalling dependencies..."
	@npm install
	@echo "Clean install completed!"

# Seed admin account
seed:
	@echo "Seeding admin account..."
	@npm run seed-admin

# Build for production
build:
	@echo "Building for production..."
	@npm run build

# Run linter
lint:
	@echo "Running ESLint..."
	@npm run lint
