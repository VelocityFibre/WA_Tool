#!/usr/bin/env python3
"""
Script to download images from the Velocity Fibre subbies WhatsApp group
using the WhatsApp MCP tools directly.
"""
import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Constants
SUBBIES_GROUP_JID = '120363417538730975@g.us'  # Velocity/fibretime subbies group JID
BASE_MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/images')

# Known image message IDs from our previous search
KNOWN_IMAGE_IDS = [
    '559719280B22A88FDBEC73C9D5CA8C53',  # May 20, 2025
]

def setup_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(BASE_MEDIA_DIR, exist_ok=True)
    print(f"Media directory set up at: {BASE_MEDIA_DIR}")

def download_image_with_mcp(message_id):
    """
    Download an image using the WhatsApp MCP command line
    
    Args:
        message_id: ID of the message containing the image
        
    Returns:
        Path to the downloaded image or None if download failed
    """
    try:
        # Use subprocess to run the mcp8_download_media command
        cmd = [
            "python3", "-c", 
            f"from mcp8_download_media import download_media; print(download_media(message_id='{message_id}', chat_jid='{SUBBIES_GROUP_JID}'))"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse the output to get the file path
            try:
                output = result.stdout.strip()
                data = json.loads(output)
                if data.get('success') and 'file_path' in data:
                    return data['file_path']
                else:
                    print(f"Download failed: {data.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                print(f"Failed to parse output: {output}")
        else:
            print(f"Command failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
    
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
    
    return None

def organize_image(source_path, message_id, date_str=None):
    """
    Organize an image into the date-based directory structure
    
    Args:
        source_path: Path to the downloaded image
        message_id: ID of the message containing the image
        date_str: Date string in YYYY-MM-DD format (optional)
        
    Returns:
        Path to the organized image or None if organization failed
    """
    try:
        # If date_str is not provided, try to extract it from the filename
        if not date_str:
            filename = os.path.basename(source_path)
            # Try to extract date from filename like "image_20250520_143730.jpg"
            if "image_" in filename and len(filename) > 15:
                date_part = filename.split("_")[1]
                if len(date_part) >= 8:
                    year = date_part[0:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    date_str = f"{year}-{month}-{day}"
        
        # If we still don't have a date, use today's date
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Create date directory if it doesn't exist
        date_dir = os.path.join(BASE_MEDIA_DIR, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        # Determine file extension
        _, ext = os.path.splitext(source_path)
        if not ext:
            ext = '.jpg'  # Default to .jpg if no extension
        
        # Create target path
        target_filename = f"image_{message_id}{ext}"
        target_path = os.path.join(date_dir, target_filename)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        print(f"Copied image to: {target_path}")
        
        return target_path
    
    except Exception as e:
        print(f"Error organizing image: {str(e)}")
        return None

def download_images_from_mcp():
    """Download images using the WhatsApp MCP tools"""
    print("Downloading images using WhatsApp MCP tools...")
    
    successful_downloads = 0
    
    # Process known image IDs
    for message_id in KNOWN_IMAGE_IDS:
        print(f"Processing image message: {message_id}")
        
        # Download the image
        source_path = download_image_with_mcp(message_id)
        if not source_path:
            print(f"Failed to download image for message: {message_id}")
            continue
        
        # Organize the image
        target_path = organize_image(source_path, message_id)
        if target_path:
            successful_downloads += 1
    
    print(f"Successfully downloaded and organized {successful_downloads} out of {len(KNOWN_IMAGE_IDS)} images")

def main():
    """Main function to download and organize WhatsApp images"""
    print("Starting WhatsApp image download and organization")
    
    # Set up directories
    setup_directories()
    
    # Download images using WhatsApp MCP
    download_images_from_mcp()
    
    # Use the direct WhatsApp MCP tool to download the image
    print("\nAlternative method: Using WhatsApp MCP directly")
    for message_id in KNOWN_IMAGE_IDS:
        print(f"To download image {message_id}, run:")
        print(f"mcp8_download_media(message_id=\"{message_id}\", chat_jid=\"{SUBBIES_GROUP_JID}\")")

if __name__ == "__main__":
    main()
