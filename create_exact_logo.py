#!/usr/bin/env python3
"""
Recreate the exact Futures logo matching the user's original design
"""
from PIL import Image, ImageDraw

def create_futures_logo_exact(size=2048):
    """
    Create the Futures logo matching the exact design provided
    Based on the geometric arrow/paper plane design pointing left
    """
    # Create white background
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    
    # The logo is a leftward-pointing arrow/paper plane made of black triangles
    # with white space creating the arrow head effect
    
    # Let's use precise coordinates based on the original design
    
    # Top large triangle (upper wing) - from top spanning most of width, angled downward
    top_wing = [
        (0, 0),                    # Top left corner
        (size, 0),                 # Top right corner  
        (size * 0.22, size * 0.33) # Point on left side
    ]
    draw.polygon(top_wing, fill='black')
    
    # Middle band (horizontal strip) - creates separation
    middle_band = [
        (size * 0.04, size * 0.33),   # Top left
        (size, size * 0.33),           # Top right
        (size, size * 0.48),           # Bottom right
        (size * 0.22, size * 0.48)     # Bottom left point
    ]
    draw.polygon(middle_band, fill='black')
    
    # Bottom left triangle (creates left edge and arrow base)
    bottom_left_section = [
        (0, size * 0.33),             # Top left
        (size * 0.22, size * 0.48),   # Middle point
        (0, size)                     # Bottom left corner
    ]
    draw.polygon(bottom_left_section, fill='black')
    
    # Large bottom right triangle (main bottom section)
    bottom_right_section = [
        (size * 0.22, size * 0.48),   # Top left point
        (size, size),                  # Bottom right corner
        (0, size)                      # Bottom left corner
    ]
    draw.polygon(bottom_right_section, fill='black')
    
    # White cutout on left side to create the arrow head point effect
    white_arrow_point = [
        (0, size * 0.24),
        (size * 0.22, size * 0.385),
        (0, size * 0.53)
    ]
    draw.polygon(white_arrow_point, fill='white')
    
    return img

def create_all_icons():
    """Generate the logo and create all icon sizes"""
    print("🎨 Creating exact Futures logo from your design...")
    print("="*60)
    
    # Create the master logo
    logo = create_futures_logo_exact(2048)
    logo.save('futures_logo_original.png', 'PNG', optimize=True)
    print("✓ Created high-resolution master logo (2048x2048)")
    
    # Icon sizes needed
    ICON_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
    
    # Directories to update
    ICON_DIRS = [
        'backend/static/icons',
        'frontend/public/icons',
        'frontend/dist/icons'
    ]
    
    total_created = 0
    
    for icon_dir in ICON_DIRS:
        print(f"\n📦 Generating icons in {icon_dir}...")
        
        for size in ICON_SIZES:
            # Resize with high-quality resampling
            resized = logo.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            output_path = f'{icon_dir}/icon-{size}x{size}.png'
            resized.save(output_path, 'PNG', optimize=True, quality=95)
            print(f"  ✓ {size}x{size}")
            total_created += 1
    
    print("\n" + "="*60)
    print(f"✅ SUCCESS! Created {total_created} icons from your exact logo")
    print(f"   ({len(ICON_SIZES)} sizes × {len(ICON_DIRS)} directories)")
    print("="*60)

if __name__ == '__main__':
    try:
        create_all_icons()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

