# WhatsApp Assistant User Guide

This guide will help you get started with the WhatsApp Assistant application, which allows you to interact with WhatsApp contacts through an AI-powered interface.

## Getting Started

### Installation

1. Make sure you have Docker installed on your computer
2. Run the installation script:

   ```bash
   ./install.sh
   ```
3. Follow the prompts to configure your LLM API key and preferences
4. Wait for the application to start

### First-Time Setup

1. Open your web browser and go to: [http://localhost:8080](http://localhost:8080)
2. You'll see a QR code on the screen
3. Open WhatsApp on your phone
4. Tap on Menu (three dots) > WhatsApp Web
5. Scan the QR code with your phone
6. The application will connect to your WhatsApp account

## Using the Application

### Main Interface

The application has three main sections:

- **Left Panel**: Shows your WhatsApp contacts and chats
- **Right Panel**: Shows the messages in the selected chat
- **Top Bar**: Contains settings and refresh buttons

### Sending Messages

1. Select a contact from the left panel
2. Type your message in the text box at the bottom
3. Click "Send" to send the message directly
4. Click "AI Send" to have the AI process and send the message

### Using AI Features

The AI can help you:

- Draft responses based on conversation context
- Generate appropriate replies
- Format messages professionally
- Translate messages to different languages

To use the AI:

1. Type your instructions in the message box
2. Click "AI Send"
3. The AI will process your instructions and send an appropriate message

Example instructions:

- "Reply politely that I'll be available tomorrow"
- "Ask about the project status in a professional way"
- "Thank them for their help and confirm the meeting time"

### Settings

Click the gear icon in the top-right corner to access settings:

- Enter or update your LLM API key
- Choose different AI models
- Configure other preferences

## Troubleshooting

### WhatsApp Not Connecting

If you see "WhatsApp Not Connected":

1. Make sure your internet connection is working
2. Try refreshing the page
3. Restart the application with:

   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. Scan the QR code again

### Messages Not Sending

If messages aren't sending:

1. Check your internet connection
2. Make sure your WhatsApp is still connected
3. Try refreshing the page
4. Check the application logs with:

   ```bash
   docker-compose logs -f
   ```

### AI Not Working

If the AI features aren't working:

1. Make sure you've entered a valid API key in Settings
2. Check that you've selected the correct LLM provider
3. Ensure your API key has sufficient credits/quota

## Getting Help

If you need additional help, please contact the IT department or refer to the detailed documentation.
