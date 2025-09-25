#!/bin/bash

# WhatsApp Assistant App Installer
# This script helps non-technical users install and run the WhatsApp Assistant app

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  WhatsApp Assistant App Installer      ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

echo -e "${GREEN}Docker and Docker Compose are installed. Great!${NC}"
echo

# Create .env file for configuration
echo -e "${YELLOW}Setting up configuration...${NC}"
echo

# Ask for LLM API key
read -p "Enter your LLM API key (leave blank to configure later): " LLM_API_KEY

# Ask for LLM provider
echo "Select LLM provider:"
echo "1. OpenAI (default)"
echo "2. Anthropic"
echo "3. Other"
read -p "Enter your choice [1-3]: " LLM_PROVIDER_CHOICE

case $LLM_PROVIDER_CHOICE in
    2)
        LLM_PROVIDER="anthropic"
        ;;
    3)
        read -p "Enter the provider name: " LLM_PROVIDER
        ;;
    *)
        LLM_PROVIDER="openai"
        ;;
esac

# Ask for LLM model
if [ "$LLM_PROVIDER" = "openai" ]; then
    echo "Select OpenAI model:"
    echo "1. GPT-4 (default)"
    echo "2. GPT-3.5-turbo"
    read -p "Enter your choice [1-2]: " LLM_MODEL_CHOICE
    
    case $LLM_MODEL_CHOICE in
        2)
            LLM_MODEL="gpt-3.5-turbo"
            ;;
        *)
            LLM_MODEL="gpt-4"
            ;;
    esac
elif [ "$LLM_PROVIDER" = "anthropic" ]; then
    echo "Select Anthropic model:"
    echo "1. claude-3-opus (default)"
    echo "2. claude-3-sonnet"
    echo "3. claude-3-haiku"
    read -p "Enter your choice [1-3]: " LLM_MODEL_CHOICE
    
    case $LLM_MODEL_CHOICE in
        2)
            LLM_MODEL="claude-3-sonnet"
            ;;
        3)
            LLM_MODEL="claude-3-haiku"
            ;;
        *)
            LLM_MODEL="claude-3-opus"
            ;;
    esac
else
    read -p "Enter the model name: " LLM_MODEL
fi

# Create .env file
echo "LLM_API_KEY=$LLM_API_KEY" > .env
echo "LLM_PROVIDER=$LLM_PROVIDER" >> .env
echo "LLM_MODEL=$LLM_MODEL" >> .env

echo -e "${GREEN}Configuration saved to .env file.${NC}"
echo

# Build and start the application
echo -e "${YELLOW}Building and starting WhatsApp Assistant...${NC}"
echo "This may take a few minutes for the first run."
echo

docker-compose up -d --build

# Check if the application started successfully
if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  WhatsApp Assistant is now running!     ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo
    echo "Open your web browser and go to: http://localhost:8080"
    echo
    echo "When you first open the app, you'll need to scan a QR code with your WhatsApp to connect."
    echo
    echo -e "${YELLOW}To stop the application, run:${NC}"
    echo "docker-compose down"
    echo
    echo -e "${YELLOW}To view logs, run:${NC}"
    echo "docker-compose logs -f"
else
    echo
    echo -e "${RED}Failed to start WhatsApp Assistant.${NC}"
    echo "Please check the error messages above."
fi
