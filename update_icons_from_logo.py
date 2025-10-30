#!/usr/bin/env python3
"""
Generate all PWA icon sizes from the actual Futures logo
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

def create_icons_from_source(source_path):
    """Create all icon sizes from the source logo"""
    print(f"📂 Loading source logo: {source_path}")
    
    # Open the source image
    try:
        img = Image.open(source_path)
    except FileNotFoundError:
        print(f"❌ Error: Source file not found at {source_path}")
        print("Please ensure the Futures logo file exists.")
        return False
    
    # Convert to RGBA for transparency support
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    print(f"✓ Source image: {img.size[0]}x{img.size[1]}, mode: {img.mode}")
    
    # Make image square if it isn't already (center it)
    width, height = img.size
    if width != height:
        print(f"⚠️  Image is not square ({width}x{height}), making it square...")
        max_size = max(width, height)
        new_img = Image.new('RGBA', (max_size, max_size), (255, 255, 255, 0))
        paste_x = (max_size - width) // 2
        paste_y = (max_size - height) // 2
        new_img.paste(img, (paste_x, paste_y))
        img = new_img
        print(f"✓ Made square: {max_size}x{max_size}")
    
    total_created = 0
    
    # Create icons for each directory
    for icon_dir in ICON_DIRS:
        if not os.path.exists(icon_dir):
            print(f"\n📁 Creating directory: {icon_dir}")
            os.makedirs(icon_dir, exist_ok=True)
        
        print(f"\n📦 Generating icons in {icon_dir}...")
        
        for size in ICON_SIZES:
            # Resize with high-quality resampling
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB with white background for better compatibility
            if resized.mode == 'RGBA':
                background = Image.new('RGB', resized.size, (255, 255, 255))
                background.paste(resized, mask=resized.split()[3])  # Use alpha channel as mask
                resized = background
            
            # Save as PNG
            output_path = os.path.join(icon_dir, f'icon-{size}x{size}.png')
            resized.save(output_path, 'PNG', optimize=True, quality=95)
            print(f"  ✓ {size}x{size}")
            total_created += 1
    
    print("\n" + "="*60)
    print(f"✅ SUCCESS! Created {total_created} icons from your Futures logo")
    print(f"   ({len(ICON_SIZES)} sizes × {len(ICON_DIRS)} directories)")
    print("="*60)
    
    return True

if __name__ == '__main__':
    # Look for the source logo
    source_logo = 'futures_logo_original.png'
    
    if not os.path.exists(source_logo):
        print(f"❌ Error: Source logo not found: {source_logo}")
        exit(1)
    
    success = create_icons_from_source(source_logo)
    exit(0 if success else 1)

