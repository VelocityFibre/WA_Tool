# WhatsApp Assistant App

A user-friendly application that integrates WhatsApp with an AI assistant, allowing non-technical users to interact with WhatsApp contacts through an AI interface.

## Features

- Connect to WhatsApp through a simple setup process
- Interact with contacts using natural language
- AI-powered responses and message handling
- Easy-to-use interface for non-technical users
- Packaged as a Docker container for simple installation

## Architecture

The application consists of three main components:

1. **WhatsApp Bridge**: Connects to WhatsApp and handles message sending/receiving
2. **AI Integration**: Connects to an LLM API for message processing
3. **User Interface**: Provides a simple way for users to interact with the system

## Installation

### Prerequisites

- Docker installed on the host machine
- Internet connection
- (Optional) LLM API key (OpenAI, Anthropic, etc.)

### Quick Start

1. Download the Docker image:
   ```
   docker pull velocityfibre/whatsapp-assistant:latest
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 velocityfibre/whatsapp-assistant:latest
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

4. Follow the on-screen instructions to set up your WhatsApp connection and LLM API key.

## Usage

1. **First-time Setup**:
   - Scan the QR code with your WhatsApp to authenticate
   - Enter your LLM API key (or use the default if provided)
   - Configure any additional settings

2. **Daily Use**:
   - Select a contact to chat with
   - Type your message or select from suggested responses
   - The AI will process and send the message
   - View responses in the chat interface

## Development

This project is built using:
- Python (FastAPI backend)
- React (Frontend)
- WhatsApp MCP for WhatsApp integration
- Docker for containerization

## License

[License details here]

## Support

For support, please contact [support contact information]
