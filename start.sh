#!/bin/bash

# Autoscience - One-Command Start Script
# Usage: ./start.sh [dev|docker|stop|status|logs|setup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           Background Scientific Cognition System         ║${NC}"
    echo -e "${BLUE}║                    Autoscience v0.1.0                    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    local missing=0
    
    # Docker
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
    else
        echo -e "${RED}✗${NC} Docker is required for Docker mode"
        missing=1
    fi
    
    # Docker Compose
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker Compose $(docker compose version | cut -d' ' -f4)"
    elif command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker Compose (legacy)"
    else
        echo -e "${RED}✗${NC} Docker Compose is required"
        missing=1
    fi
    
    # Python (for dev mode)
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✓${NC} Python $(python3 --version | cut -d' ' -f2)"
    fi
    
    # Node.js (for dev mode)
    if command -v node &> /dev/null; then
        echo -e "${GREEN}✓${NC} Node.js $(node --version)"
    fi
    
    if [ $missing -eq 1 ]; then
        echo ""
        echo -e "${RED}Missing prerequisites. Please install them first.${NC}"
        exit 1
    fi
    echo ""
}

setup_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env from template...${NC}"
        cat > .env << 'EOF'
# Autoscience Environment Configuration

# Database
POSTGRES_PASSWORD=autoscience
POSTGRES_PORT=5432

# Redis
REDIS_PORT=6379

# Backend
BACKEND_PORT=8000
APP_DEBUG=false

# Frontend
FRONTEND_PORT=3000

# LLM Providers (at least one required)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LOCAL_LLM_BASE_URL=http://host.docker.internal:11434
DEFAULT_LLM_PROVIDER=openai

# Academic Sources (optional, improves rate limits)
SEMANTIC_SCHOLAR_API_KEY=
UNPAYWALL_EMAIL=
EOF
        echo -e "${GREEN}Created .env file. Please add your API keys.${NC}"
    fi
}

start_docker() {
    print_header
    echo -e "${BLUE}Starting with Docker Compose...${NC}"
    echo ""
    
    check_prerequisites
    setup_env
    
    # Build and start services
    echo -e "${YELLOW}Building and starting services...${NC}"
    docker compose -f docker/docker-compose.yml up -d --build
    
    echo ""
    echo -e "${GREEN}Services started!${NC}"
    echo ""
    echo -e "Frontend:   ${BLUE}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "Backend:    ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "API Docs:   ${BLUE}http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "PostgreSQL: ${BLUE}localhost:${POSTGRES_PORT}${NC}"
    echo -e "Redis:      ${BLUE}localhost:${REDIS_PORT}${NC}"
    echo ""
    echo -e "${YELLOW}Tip: Use './start.sh logs' to view logs${NC}"
    echo -e "${YELLOW}Tip: Use './start.sh stop' to stop all services${NC}"
    echo ""
}

start_dev() {
    print_header
    echo -e "${BLUE}Starting in development mode with hot-reload...${NC}"
    echo ""
    
    check_prerequisites
    setup_env
    
    # Start services with hot-reload
    echo -e "${YELLOW}Starting development services...${NC}"
    docker compose -f docker/docker-compose.dev.yml up -d --build
    
    echo ""
    echo -e "${GREEN}Development services started with hot-reload!${NC}"
    echo ""
    echo -e "Frontend:   ${BLUE}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "Backend:    ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "API Docs:   ${BLUE}http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "PostgreSQL: ${BLUE}localhost:5433${NC}"
    echo -e "Redis:      ${BLUE}localhost:6380${NC}"
    echo ""
    echo -e "${YELLOW}Hot-reload is enabled:${NC}"
    echo -e "  - Backend: Edit files in backend/app/ → auto-restarts"
    echo -e "  - Frontend: Edit files in frontend/src/ → auto-refreshes"
    echo ""
    echo -e "${YELLOW}Tip: Use './start.sh logs' to view logs${NC}"
    echo -e "${YELLOW}Tip: Use './start.sh stop' to stop all services${NC}"
    echo ""
}

stop_dev() {
    local backend_pid=$1
    local frontend_pid=$2
    
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    
    [ -n "$backend_pid" ] && kill $backend_pid 2>/dev/null
    [ -n "$frontend_pid" ] && kill $frontend_pid 2>/dev/null
    
    echo -e "${GREEN}Services stopped.${NC}"
}

stop_docker() {
    print_header
    echo -e "${YELLOW}Stopping Docker services...${NC}"
    # Stop both production and dev compose files
    docker compose -f docker/docker-compose.yml down 2>/dev/null || true
    docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || true
    echo -e "${GREEN}Services stopped.${NC}"
}

show_status() {
    print_header
    echo -e "${BLUE}Docker Services Status:${NC}"
    echo ""
    echo -e "${YELLOW}Production services:${NC}"
    docker compose -f docker/docker-compose.yml ps 2>/dev/null || echo "  Not running"
    echo ""
    echo -e "${YELLOW}Development services:${NC}"
    docker compose -f docker/docker-compose.dev.yml ps 2>/dev/null || echo "  Not running"
    echo ""
}

show_logs() {
    # Try dev first, then production
    if docker compose -f docker/docker-compose.dev.yml ps 2>/dev/null | grep -q running; then
        docker compose -f docker/docker-compose.dev.yml logs -f
    else
        docker compose -f docker/docker-compose.yml logs -f
    fi
}

show_help() {
    print_header
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  docker    Start all services with Docker (production-like)"
    echo "  dev       Start in development mode with hot-reload"
    echo "  stop      Stop all services"
    echo "  status    Show service status"
    echo "  logs      View logs (Docker mode)"
    echo "  setup     Initial setup (create .env files)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh docker    # Production-like mode"
    echo "  ./start.sh dev       # Development with hot-reload"
    echo "  ./start.sh stop      # Stop everything"
    echo ""
}

# Main
case "${1:-help}" in
    docker)
        start_docker
        ;;
    dev)
        start_dev
        ;;
    stop)
        stop_docker
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    setup)
        setup_env
        ;;
    help|*)
        show_help
        ;;
esac
