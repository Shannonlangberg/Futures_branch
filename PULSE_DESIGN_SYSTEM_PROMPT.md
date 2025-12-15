# Futures PULSE Design System Prompt

## Overview
A modern, dark-themed design system featuring glassmorphism, vibrant gradients, and smooth animations. The design balances professionalism with energetic visual elements, creating an engaging and contemporary user experience.

---

## Color Palette

### Primary Background Colors
- **Base Dark**: `#0f172a` (slate-900)
- **Secondary Dark**: `#1e293b` (slate-800)
- **Tertiary Dark**: `#334155` (slate-700)

### Accent Colors (Primary Brand Colors)
- **Blue Primary**: `#3b82f6` (blue-500) - Primary action color
- **Blue Secondary**: `#2563eb` (blue-600) - Hover states
- **Cyan**: `#06b6d4` (cyan-500) - Secondary accents
- **Purple**: `#a855f7` (purple-500) - Interactive elements
- **Pink**: `#ec4899` (pink-500) - Accent highlights

### Semantic Colors
- **Success/Emerald**: `#10b981` (emerald-500)
- **Warning/Orange**: `#f97316` (orange-500)
- **Error/Red**: `#ef4444` (red-500)
- **Info/Blue**: `#3b82f6` (blue-500)

### Text Colors
- **Primary Text**: `#ffffff` (white)
- **Secondary Text**: `rgba(255, 255, 255, 0.8)` (white/80)
- **Tertiary Text**: `rgba(255, 255, 255, 0.6)` (white/60)
- **Muted Text**: `#94a3b8` (slate-400)
- **Subtle Text**: `#64748b` (slate-500)

### Glassmorphism Overlays
- **Glass Background**: `rgba(51, 65, 85, 0.5)` with `backdrop-blur-sm`
- **Glass Border**: `rgba(51, 65, 85, 0.5)` (slate-700/50)
- **Glass Light**: `rgba(255, 255, 255, 0.05)` to `rgba(255, 255, 255, 0.15)`

---

## Typography

### Font Family
- **Primary**: `'Inter', system-ui, sans-serif`
- **Weights**: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)

### Type Scale
- **H1/Display**: `text-4xl` to `text-5xl` (2.25rem - 3rem), `font-bold`
- **H2/Section Headers**: `text-3xl` (1.875rem), `font-bold`
- **H3/Card Titles**: `text-xl` to `text-2xl` (1.25rem - 1.5rem), `font-bold`
- **Body Large**: `text-lg` (1.125rem), `font-medium`
- **Body Regular**: `text-base` (1rem), `font-normal`
- **Body Small**: `text-sm` (0.875rem), `font-medium`
- **Caption**: `text-xs` (0.75rem), `font-normal`

### Line Heights
- Tight headings: `leading-tight`
- Body text: Default line-height
- Loose text: `leading-relaxed`

---

## Spacing System

### Standard Spacing Scale
- **xs**: `0.5rem` (8px)
- **sm**: `0.75rem` (12px)
- **md**: `1rem` (16px)
- **lg**: `1.5rem` (24px)
- **xl**: `2rem` (32px)
- **2xl**: `3rem` (48px)
- **3xl**: `4rem` (64px)

### Component Padding
- **Cards**: `p-6` to `p-8` (24px - 32px)
- **Buttons**: `px-6 py-4` to `px-8 py-4` (24-32px horizontal, 16px vertical)
- **Inputs**: `px-4 py-3` to `px-6 py-4`
- **Sidebar**: `px-4 py-6`

---

## Component Patterns

### Buttons

#### Primary Button
```
- Background: Gradient from accent color to complementary accent
- Examples: 
  * Blue: `bg-gradient-to-r from-blue-600 to-cyan-600`
  * Purple: `bg-gradient-to-r from-purple-600 to-pink-600`
- Text: White, semibold
- Padding: `px-6 py-4` to `px-8 py-4`
- Border Radius: `rounded-2xl` (16px)
- Shadow: `shadow-2xl` with colored shadow on hover
- Hover: `hover:scale-105`, `hover:shadow-blue-500/25` (colored shadow)
- Transition: `transition-all duration-300`
```

#### Secondary Button
```
- Background: Glassmorphism with semi-transparent overlay
- Style: `bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-sm`
- Border: `border border-purple-400/20`
- Text: White
- Hover: Same scale and shadow effects as primary
```

#### Icon Button
```
- Circular or rounded square
- Size: `w-10 h-10` to `w-12 h-12`
- Background: `bg-white/10 hover:bg-white/20`
- Icon size: `h-5 w-5` to `h-6 w-6`
```

### Cards

#### Standard Card
```
- Background: Glassmorphism effect
  * `bg-white/5 backdrop-blur-sm` or
  * `bg-slate-800/50 backdrop-blur-sm`
- Border: `border border-white/10` or `border-slate-700/50`
- Border Radius: `rounded-2xl` (16px)
- Padding: `p-6` to `p-8`
- Shadow: `shadow-2xl`
- Hover Effects: 
  * `hover:shadow-blue-500/10` (colored shadow)
  * Optional `hover:scale-105` for interactive cards
```

#### Gradient Card
```
- Background: Gradient with opacity
  * `bg-gradient-to-br from-blue-500/20 to-blue-600/20`
- Border: Matching colored border with opacity
  * `border border-blue-400/20`
- Additional overlay on hover with opacity transition
```

### Input Fields

#### Text Input
```
- Background: `bg-white/10 backdrop-blur-sm` or `bg-slate-700/50`
- Border: `border border-white/20` or `border-slate-600/50`
- Border Radius: `rounded-xl` (12px)
- Padding: `px-4 py-3` to `px-6 py-4`
- Text: White with `placeholder-white/60`
- Focus:
  * `focus:ring-2 focus:ring-blue-400/20`
  * `focus:border-blue-400/50`
  * `focus:bg-white/15`
- Transition: `transition-all duration-300`
```

#### Select/Dropdown
```
- Same styling as text input
- Custom scrollbar styling (see scrollbar section)
```

---

## Layout Patterns

### Background

#### Main Background
```
- Base: `bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900`
- Optional animated gradient orbs:
  * Large blurred circles with accent colors at low opacity (10-5%)
  * Positioned at corners and center
  * Pulse animation
```

#### Glassmorphism Overlay
```
- Semi-transparent backgrounds with backdrop blur
- Creates depth and layering effect
- Used for modals, cards, sidebars, and navigation
```

### Sidebar/Navigation

#### Sidebar Container
```
- Background: `bg-slate-900 border-r border-slate-700/50`
- Width: `w-64` (256px)
- Fixed positioning on desktop
- Scrollable content area with custom scrollbar
```

#### Navigation Items
```
- Active State:
  * `bg-gradient-to-r from-blue-600/20 to-purple-600/20`
  * `border border-blue-500/30`
  * `shadow-lg shadow-blue-500/20`
  * Icon and text in white/blue-400

- Inactive State:
  * `text-slate-300 hover:text-white`
  * `hover:bg-slate-800/50`
  * Icon in `text-slate-400`
```

---

## Visual Effects

### Shadows

#### Standard Shadows
- **Small**: `shadow-lg`
- **Medium**: `shadow-2xl`
- **Colored Shadows** (on hover):
  - `hover:shadow-blue-500/25`
  - `hover:shadow-purple-500/25`
  - Shadow opacity typically 20-30%

### Glows

#### Glow Effects
- Used for active states and important elements
- Examples:
  - `shadow-lg shadow-red-500/25` (recording/active state)
  - `shadow-lg shadow-blue-500/25` (idle/ready state)

### Gradients

#### Background Gradients
- **Primary**: `from-blue-600 via-purple-600 to-pink-600`
- **Card Overlays**: Single color with opacity gradient
- **Borders**: Gradient borders for active states

#### Text Gradients (when used)
- `bg-gradient-to-r from-blue-400 to-purple-400`
- Applied with `bg-clip-text text-transparent`

---

## Animations & Transitions

### Standard Transitions
- **Duration**: `duration-300` (300ms) standard, `duration-500` for slower transitions
- **Easing**: Default (ease-in-out)
- **Properties**: `transition-all` for comprehensive transitions

### Hover Effects
- **Scale**: `hover:scale-105` (5% scale up)
- **Opacity**: `hover:opacity-80` for subtle fade
- **Shadow**: Colored shadow intensification on hover
- **Transform**: `hover:-translate-y-1` for lift effect on cards

### Loading States
- **Pulse**: `animate-pulse` for loading indicators
- **Spin**: `animate-spin` for rotating elements (spinners)
- **Custom Keyframes**: `fadeIn`, `slideUp` defined in Tailwind config

### Active States
- **Recording/Active**: Pulsing animation with colored shadow
- **Button Press**: Scale down slightly or maintain scale-up

---

## Border Radius

### Standard Radius Values
- **Small**: `rounded-lg` (8px) - buttons, small elements
- **Medium**: `rounded-xl` (12px) - inputs, cards
- **Large**: `rounded-2xl` (16px) - main cards, large buttons
- **Extra Large**: `rounded-3xl` (24px) - modals, hero sections
- **Full**: `rounded-full` - circular elements, pills

---

## Scrollbar Styling

### Custom Scrollbar
```
- Width: 6px
- Track: `#1e293b` (slate-800) with rounded corners
- Thumb: `#475569` (slate-600) with rounded corners
- Thumb Hover: `#64748b` (slate-500)
- Border Radius: 3px
```

---

## Icons

### Icon Library
- **Heroicons** (24px outline style)
- **Size**: `h-5 w-5` (20px) standard, `h-6 w-6` (24px) for emphasis
- **Color**: Inherits text color or specific accent colors
- **Spacing**: `mr-3` (12px) spacing from text

### Emoji Usage
- Used for visual interest and quick recognition
- Sizes: `text-xl` to `text-4xl` depending on context
- Common emojis: ⛪ 📊 📈 🎯 👥 💰 🤖 🧒 📅 ⚡ 💬

---

## Modal/Dialog Patterns

### Modal Container
```
- Overlay: `fixed inset-0 bg-black/60 backdrop-blur-sm`
- Container: 
  * `bg-gradient-to-br from-slate-900/95 to-slate-800/95`
  * `backdrop-blur-xl`
  * `rounded-3xl` (24px)
  * `border border-white/10`
  * `shadow-2xl`
- Max Width: `max-w-5xl` for large modals
- Centered with flexbox
```

### Modal Header
- Large icon/emoji (32-48px)
- Bold title (`text-3xl font-bold`)
- Close button in top right (icon button style)

---

## Grid & Layout

### Standard Grid Patterns
- **Card Grid**: `grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6`
- **Dashboard**: Responsive grid with breakpoints
- **Spacing**: Consistent `gap-6` (24px) between grid items

### Container Widths
- **Full Width**: Default (full viewport)
- **Constrained**: `max-w-7xl mx-auto` for content
- **Narrow Content**: `max-w-4xl mx-auto` for forms/articles

---

## Accessibility Considerations

### Focus States
- Visible focus rings: `focus:ring-2 focus:ring-blue-500/20`
- High contrast for interactive elements
- Clear hover states

### Color Contrast
- White text on dark backgrounds meets WCAG AA standards
- Accent colors used for emphasis, not information alone

---

## Key Design Principles

1. **Glassmorphism First**: Use semi-transparent overlays with backdrop blur for depth
2. **Gradient Accents**: Vibrant gradients for buttons and important elements
3. **Smooth Animations**: All interactions should feel fluid (300ms standard)
4. **Layered Depth**: Multiple z-levels with shadows and glows
5. **Consistent Spacing**: Use the spacing scale religiously
6. **Dark Theme**: Dark backgrounds with bright accent colors
7. **Modern Rounded**: Generous border radius (2xl standard)
8. **Interactive Feedback**: Clear hover, active, and focus states
9. **Visual Hierarchy**: Use size, color, and shadow to create clear hierarchy
10. **Energetic but Professional**: Balance fun visual elements with clean, readable layouts

---

## Example Component Combinations

### Hero Section Button
```
className="group relative bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-8 py-4 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-2xl hover:shadow-blue-500/25 overflow-hidden"
```

### Stat Card
```
className="group relative bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-sm rounded-2xl p-6 border border-blue-400/20 shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 hover:scale-105"
```

### Glass Input
```
className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition-all duration-300"
```

---

## Responsive Breakpoints

- **Mobile**: Default (< 640px)
- **Tablet**: `md:` (640px+)
- **Desktop**: `lg:` (1024px+)
- **Large Desktop**: `xl:` (1280px+)
- **Extra Large**: `2xl:` (1536px+)

---

## Implementation Notes

- Built with **Tailwind CSS** utility-first approach
- Uses **Heroicons** for icon system
- **Inter** font loaded from Google Fonts
- Backdrop blur effects require modern browser support
- Custom CSS classes defined in `index.css` for reusable patterns
- Animation support via Tailwind's built-in animation utilities

---

This design system creates a cohesive, modern interface that feels both professional and engaging, perfect for a church management and engagement platform.











