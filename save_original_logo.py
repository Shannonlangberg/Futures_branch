#!/usr/bin/env python3
"""
Recreate the exact Futures logo from the user's image
Based on careful analysis of the original geometric design
"""
from PIL import Image, ImageDraw

def create_exact_futures_logo(size=2048):
    """
    Recreate the Futures logo to match the original exactly
    Black geometric arrow/paper plane on white background
    """
    # Create white background
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    
    # Analyze the original: it's a leftward-pointing arrow made of triangular shapes
    # The design has 3 main black triangular sections with white space creating the arrow
    
    # Scale factor
    s = size / 2048
    
    # Top triangle (upper wing) - extends from left to right, angled down
    top_triangle = [
        (int(s * 100), int(s * 50)),       # Top left corner
        (int(s * 1950), int(s * 50)),      # Top right corner  
        (int(s * 100), int(s * 650))       # Left point
    ]
    draw.polygon(top_triangle, fill='black')
    
    # Middle triangle/band - horizontal-ish strip
    middle_band = [
        (int(s * 100), int(s * 650)),      # Top left
        (int(s * 1950), int(s * 650)),     # Top right
        (int(s * 100), int(s * 950))       # Bottom left
    ]
    draw.polygon(middle_band, fill='black')
    
    # Bottom left small triangle
    bottom_left = [
        (int(s * 100), int(s * 950)),      # Top point
        (int(s * 100), int(s * 1950)),     # Bottom left
        (int(s * 450), int(s * 950))       # Right point
    ]
    draw.polygon(bottom_left, fill='black')
    
    # Large bottom right triangle
    bottom_right = [
        (int(s * 450), int(s * 950)),      # Top left point
        (int(s * 1950), int(s * 1950)),    # Bottom right
        (int(s * 100), int(s * 1950))      # Bottom left
    ]
    draw.polygon(bottom_right, fill='black')
    
    # Cut out white triangular space on the left to create arrow point
    white_cutout = [
        (int(s * 100), int(s * 500)),
        (int(s * 450), int(s * 800)),
        (int(s * 100), int(s * 1100))
    ]
    draw.polygon(white_cutout, fill='white')
    
    return img

if __name__ == '__main__':
    print("🎨 Creating exact Futures logo...")
    logo = create_exact_futures_logo(2048)
    logo.save('futures_logo_original.png', 'PNG', optimize=True)
    print("✓ Saved as futures_logo_original.png")
    
    # Also create a preview
    preview = logo.resize((512, 512), Image.Resampling.LANCZOS)
    preview.save('futures_logo_preview.png', 'PNG', optimize=True)
    print("✓ Saved preview as futures_logo_preview.png")
    print("\nNow run: python3 update_icons_from_logo.py")

