# Pulse Design System - Styling Prompt for Cursor Agent

Use this prompt to match the Futures PULSE design system, especially the navigation bar and overall visual styling.

## Core Design Philosophy

**Modern dark theme with glassmorphism, vibrant gradients, and smooth animations.** The design balances professionalism with energetic visual elements. All interactions should feel fluid and responsive.

---

## Navigation Bar Styling (CRITICAL - Match This Exactly)

### Top Navigation Bar
```jsx
// Fixed top bar with glassmorphism
<nav className="fixed top-0 left-0 right-0 z-30 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700/50">
  <div className="flex items-center justify-between h-16 px-4 lg:px-6">
    {/* Navigation items */}
  </div>
</nav>
```

**Key Properties:**
- Background: `bg-slate-900/95` (95% opacity dark slate)
- Backdrop blur: `backdrop-blur-sm`
- Border: `border-b border-slate-700/50` (bottom border, 50% opacity)
- Height: `h-16` (64px)
- Z-index: `z-30` (below modals but above content)
- Position: `fixed top-0 left-0 right-0`

### Active Navigation Item
```jsx
className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20"
```

**Active State Breakdown:**
- Background: Gradient from `blue-600/20` to `purple-600/20` (20% opacity)
- Text: `text-white`
- Border: `border border-blue-500/30` (30% opacity blue)
- Shadow: `shadow-lg shadow-blue-500/20` (colored shadow with 20% opacity)
- Icon color: `text-blue-400`

### Inactive Navigation Item
```jsx
className="text-slate-300 hover:text-white hover:bg-slate-800/50"
```

**Inactive State Breakdown:**
- Text: `text-slate-300` (default), `hover:text-white`
- Background: `hover:bg-slate-800/50` (50% opacity on hover)
- Icon color: `text-slate-400`
- Transition: `transition-all duration-200`

### Sidebar Navigation (Left Sidebar)

**Sidebar Container:**
```jsx
className="fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-700/50"
```

**Sidebar Properties:**
- Width: `w-64` (256px)
- Background: `bg-slate-900`
- Border: `border-r border-slate-700/50` (right border, 50% opacity)
- Position: `fixed inset-y-0 left-0`
- Z-index: `z-50` (above top nav)

**Sidebar Logo/Brand Header:**
```jsx
className="flex h-16 items-center justify-between px-6 border-b border-slate-700/50"
```
- Height: `h-16` (64px)
- Padding: `px-6` (24px horizontal)
- Border: `border-b border-slate-700/50`

**Sidebar Navigation Items (Same as Top Nav):**
- Active: `bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20`
- Inactive: `text-slate-300 hover:text-white hover:bg-slate-800/50`
- Padding: `px-4 py-2.5`
- Border radius: `rounded-lg`
- Icon spacing: `mr-3` (12px margin-right)
- Icon size: `h-5 w-5` (20px)

**Sidebar Footer (User Info):**
```jsx
className="p-4 border-t border-slate-700/50 space-y-3 bg-slate-900"
```
- User info card: `bg-slate-800/50 rounded-lg px-4 py-2`
- Logout button: `text-red-300 hover:text-red-200 hover:bg-red-900/20`

---

## Color Palette (Use These Exact Values)

### Background Colors
- **Base Dark**: `#0f172a` → `bg-slate-900`
- **Secondary Dark**: `#1e293b` → `bg-slate-800`
- **Tertiary Dark**: `#334155` → `bg-slate-700`

### Accent Colors
- **Blue Primary**: `#3b82f6` → `blue-500`
- **Blue Secondary**: `#2563eb` → `blue-600`
- **Purple**: `#a855f7` → `purple-500`
- **Cyan**: `#06b6d4` → `cyan-500`
- **Pink**: `#ec4899` → `pink-500`

### Text Colors
- **Primary**: `#ffffff` → `text-white`
- **Secondary**: `rgba(255, 255, 255, 0.8)` → `text-white/80` or `text-slate-300`
- **Tertiary**: `rgba(255, 255, 255, 0.6)` → `text-white/60` or `text-slate-400`
- **Muted**: `#94a3b8` → `text-slate-400`
- **Subtle**: `#64748b` → `text-slate-500`

### Glassmorphism Colors
- **Glass Background**: `rgba(51, 65, 85, 0.5)` → `bg-slate-700/50` with `backdrop-blur-sm`
- **Glass Border**: `rgba(51, 65, 85, 0.5)` → `border-slate-700/50`
- **Glass Light**: `rgba(255, 255, 255, 0.05)` to `rgba(255, 255, 255, 0.15)` → `bg-white/5` to `bg-white/15`

---

## Typography

### Font Family
```css
font-family: 'Inter', system-ui, sans-serif;
```

### Type Scale
- **H1/Display**: `text-4xl` to `text-5xl`, `font-bold`
- **H2/Section**: `text-3xl`, `font-bold`
- **H3/Card Titles**: `text-xl` to `text-2xl`, `font-bold`
- **Body Large**: `text-lg`, `font-medium`
- **Body Regular**: `text-base`, `font-normal`
- **Body Small**: `text-sm`, `font-medium`
- **Caption**: `text-xs`, `font-normal`

---

## Component Patterns

### Buttons

**Primary Button:**
```jsx
className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-2xl hover:shadow-blue-500/25"
```

**Secondary Button:**
```jsx
className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-sm border border-purple-400/20 text-white px-6 py-4 rounded-2xl hover:scale-105 transition-all duration-300"
```

**Icon Button:**
```jsx
className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center transition-all duration-300"
```

### Cards

**Standard Glass Card:**
```jsx
className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-2xl hover:shadow-blue-500/10 transition-all duration-300"
```

**Gradient Card:**
```jsx
className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-sm border border-blue-400/20 rounded-2xl p-6 shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 hover:scale-105"
```

### Input Fields

**Text Input:**
```jsx
className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400/20 focus:border-blue-400/50 focus:bg-white/15 transition-all duration-300"
```

---

## Layout Patterns

### Main Background
```jsx
className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 min-h-screen"
```

### Container Spacing
- **Page Padding**: `p-6` (24px)
- **Card Padding**: `p-6` to `p-8` (24px - 32px)
- **Section Spacing**: `space-y-6` (24px vertical gap)

### Sidebar Offset (for main content)
```jsx
className="lg:pl-64 pt-16"
```
- Left padding: `lg:pl-64` (256px on large screens for sidebar)
- Top padding: `pt-16` (64px for top navigation bar)

---

## Visual Effects

### Shadows
- **Standard**: `shadow-2xl`
- **Colored on Hover**: `hover:shadow-blue-500/25` (25% opacity)
- **Active State**: `shadow-lg shadow-blue-500/20` (20% opacity)

### Transitions
- **Standard**: `transition-all duration-300`
- **Fast**: `transition-all duration-200`
- **Slow**: `transition-all duration-500`

### Hover Effects
- **Scale**: `hover:scale-105` (5% larger)
- **Lift**: `hover:-translate-y-1` (slight upward movement)
- **Shadow Intensification**: Colored shadow on hover

### Border Radius
- **Small**: `rounded-lg` (8px)
- **Medium**: `rounded-xl` (12px)
- **Large**: `rounded-2xl` (16px) - **Most common**
- **Extra Large**: `rounded-3xl` (24px)
- **Full**: `rounded-full`

---

## Icons

### Icon Library
- **Heroicons** (24px outline style)
- **Size**: `h-5 w-5` (20px) standard, `h-6 w-6` (24px) for emphasis
- **Spacing from text**: `mr-3` (12px)
- **Color**: Inherits text color or specific accent colors

### Icon Colors in Navigation
- **Active**: `text-blue-400`
- **Inactive**: `text-slate-400`

---

## Scrollbar Styling

```css
/* Custom scrollbar */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: #1e293b; /* slate-800 */
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #475569; /* slate-600 */
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: #64748b; /* slate-500 */
}
```

Apply to scrollable containers:
```jsx
className="overflow-y-auto scrollbar-thin"
```

---

## Responsive Breakpoints

- **Mobile**: Default (< 640px)
- **Tablet**: `md:` (640px+)
- **Desktop**: `lg:` (1024px+)
- **Large Desktop**: `xl:` (1280px+)
- **Extra Large**: `2xl:` (1536px+)

---

## Key Implementation Rules

1. **Navigation Bar Must Have:**
   - Fixed positioning at top
   - `bg-slate-900/95 backdrop-blur-sm`
   - `border-b border-slate-700/50`
   - Active items with gradient background and colored shadow
   - Smooth transitions on all interactions

2. **Sidebar Must Have:**
   - Fixed positioning on left
   - `w-64` width
   - `bg-slate-900` background
   - Same active/inactive styling as top nav
   - Scrollable navigation area with custom scrollbar

3. **All Interactive Elements:**
   - Use `transition-all duration-200` or `duration-300`
   - Include hover states
   - Use colored shadows for active/important states
   - Scale effects: `hover:scale-105`

4. **Glassmorphism Everywhere:**
   - Use `backdrop-blur-sm` or `backdrop-blur-xl`
   - Semi-transparent backgrounds with opacity (e.g., `/50`, `/20`)
   - Subtle borders with opacity

5. **Gradients for Accents:**
   - Buttons: `from-blue-600 to-cyan-600` or `from-purple-600 to-pink-600`
   - Active states: `from-blue-600/20 to-purple-600/20`
   - Always use opacity for overlays

6. **Spacing Consistency:**
   - Use Tailwind spacing scale (4px increments)
   - Common: `p-4`, `p-6`, `p-8` for padding
   - Common: `space-y-2`, `space-y-4`, `space-y-6` for gaps

---

## Example: Complete Navigation Item Component

```jsx
<Link
  to="/dashboard"
  className={`
    flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
    ${isActive
      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20'
      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
    }
  `}
>
  <DocumentChartBarIcon className={`h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
  <span>Dashboard</span>
</Link>
```

---

## Tailwind Config Requirements

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        slate: {
          // Use standard Tailwind slate palette
          50: '#f8fafc',
          // ... through 900: '#0f172a'
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
}
```

---

## CSS Requirements

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: 'Inter', system-ui, sans-serif;
  }
  
  body {
    @apply bg-slate-900 text-white;
  }
}
```

---

## Quick Reference Checklist

When implementing navigation or any component, ensure:

- [ ] Dark theme: `bg-slate-900` or `bg-slate-800`
- [ ] Glassmorphism: `backdrop-blur-sm` with semi-transparent backgrounds
- [ ] Active states: Gradient background (`from-blue-600/20 to-purple-600/20`) with colored shadow
- [ ] Transitions: `transition-all duration-200` or `duration-300`
- [ ] Border radius: `rounded-2xl` for cards, `rounded-lg` for nav items
- [ ] Shadows: `shadow-2xl` with colored hover shadows
- [ ] Icons: Heroicons, `h-5 w-5`, proper spacing (`mr-3`)
- [ ] Text colors: `text-white` for primary, `text-slate-300` for secondary
- [ ] Hover effects: Scale (`hover:scale-105`) and color changes
- [ ] Custom scrollbar: Thin (6px), slate colors

---

**Remember:** The navigation bar is the most visible component. Match the exact classes and styling patterns shown above for consistency with the Pulse design system.








