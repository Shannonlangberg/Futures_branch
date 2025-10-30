#!/usr/bin/env python3
"""
Generate PWA icons from the Futures logo
"""
from PIL import Image
import os

# Icon sizes needed for PWA
ICON_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]

# Paths to update
ICON_DIRS = [
    'backend/static/icons',
    'frontend/public/icons',
    'frontend/dist/icons'
]

def create_icons(source_image_path):
    """Create all icon sizes from source image"""
    print(f"Loading source image: {source_image_path}")
    
    # Open the source image
    img = Image.open(source_image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    print(f"Source image size: {img.size}")
    print(f"Source image mode: {img.mode}")
    
    # Create icons for each directory
    for icon_dir in ICON_DIRS:
        if not os.path.exists(icon_dir):
            print(f"Creating directory: {icon_dir}")
            os.makedirs(icon_dir, exist_ok=True)
        
        print(f"\nGenerating icons in {icon_dir}...")
        
        for size in ICON_SIZES:
            # Resize image
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            output_path = os.path.join(icon_dir, f'icon-{size}x{size}.png')
            resized.save(output_path, 'PNG', optimize=True)
            print(f"  ✓ Created {output_path}")
    
    print("\n✅ All icons generated successfully!")

if __name__ == '__main__':
    # Use the uploaded logo
    source_logo = 'futures_logo_source.png'
    
    if not os.path.exists(source_logo):
        print(f"❌ Error: Source logo not found at {source_logo}")
        print("Please ensure the Futures logo is saved as 'futures_logo_source.png'")
        exit(1)
    
    create_icons(source_logo)

