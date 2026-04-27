---
name: Luminous Management
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#41484a'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#72787a'
  outline-variant: '#c1c7ca'
  surface-tint: '#45636b'
  primary: '#14333b'
  on-primary: '#ffffff'
  primary-container: '#2c4a52'
  on-primary-container: '#99b9c2'
  inverse-primary: '#acccd5'
  secondary: '#51606c'
  on-secondary: '#ffffff'
  secondary-container: '#d4e5f3'
  on-secondary-container: '#576672'
  tertiary: '#452916'
  on-tertiary: '#ffffff'
  tertiary-container: '#5e3f2a'
  on-tertiary-container: '#d6ab90'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c8e8f2'
  primary-fixed-dim: '#acccd5'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#2d4b53'
  secondary-fixed: '#d4e5f3'
  secondary-fixed-dim: '#b8c9d6'
  on-secondary-fixed: '#0d1d27'
  on-secondary-fixed-variant: '#394954'
  tertiary-fixed: '#ffdcc7'
  tertiary-fixed-dim: '#eabda2'
  on-tertiary-fixed: '#2d1605'
  on-tertiary-fixed-variant: '#5f402b'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  section-gap: 48px
  element-gap: 12px
---

## Brand & Style

The design system is defined by a "Luminous Workspace" aesthetic—a synthesis of high-end minimalism and glassmorphism. It is designed to evoke a sense of calm, clarity, and precision, specifically tailored for the high-stakes environment of shift management. The emotional response is one of organized tranquility, reducing the cognitive load of complex scheduling tasks through visual lightness.

The style utilizes translucency to maintain spatial awareness within the application. By using frosted glass effects for secondary panels and navigation, the system ensures that the user never feels "trapped" in a sub-menu, maintaining a constant connection to the primary workspace background. The result is an airy, professional atmosphere that feels more like a sophisticated tool than a rigid corporate database.

## Colors

The palette is anchored by "Deep Slate Teal" for primary actions and "Soft Fog" greys for structural elements. 

- **Primary:** A sophisticated Deep Slate Teal used for high-priority interactions, active states, and brand identifiers.
- **Surface:** The foundation is a pristine, slightly cool white. 
- **Translucent:** Glass elements use a white base at 70% opacity with a high saturation background blur.
- **Neutral:** A range of soft greys (Slate 50 to Slate 300) are used for secondary text and low-contrast dividers to maintain the airy feel without introducing harsh lines.

## Typography

This design system relies on **Inter** for its utilitarian precision and modern neutrality. The typographic scale is restrained to prevent visual clutter in data-heavy shift views.

- **Headlines:** Use medium weights with slight negative letter-spacing for a high-end, editorial feel.
- **Body Text:** Sized at 15px for optimal readability on desktop monitors, with a generous 1.6 line-height to enhance the "airy" quality.
- **Labels:** Small, uppercase labels with increased tracking are used for metadata and category headers to provide clear hierarchy without taking up significant real estate.

## Layout & Spacing

The layout philosophy follows a **Fixed-Fluid Hybrid** model. Navigation and sidebars are fixed-width translucent panels, while the central workspace (the shift calendar or dashboard) is fluid, expanding to maximize the view of the schedule.

- **Grid:** A 12-column grid is used for the main dashboard content.
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **Whitespace:** Significant internal padding (32px) within containers is required to maintain the "Luminous" feel. Content should never feel cramped against the edges of its glass container.

## Elevation & Depth

Depth is conveyed through **refractive layers** rather than heavy shadows.

1.  **Base Layer:** Solid cool-grey background (the "desk").
2.  **Mid Layer:** Frosted glass panels (backdrop-filter: blur(20px)) with a 1px inner white border to simulate the edge of the glass.
3.  **Top Layer:** Subtle, highly diffused ambient shadows (0px 10px 30px rgba(0,0,0,0.04)) are used only for floating elements like modals or active dropdowns.
4.  **Interaction:** Hovering over a shift card should slightly increase the backdrop blur and the opacity of the inner border, creating a tactile "lift" effect without physical displacement.

## Shapes

The shape language is consistently "Rounded" (Level 2) to soften the professional environment and make the interface feel approachable.

- **Standard Elements:** Buttons and input fields use a 0.5rem (8px) radius.
- **Containers:** Large glass panels and cards use a 1rem (16px) radius.
- **Shift Blocks:** Use the standard 8px radius to maintain a clean, grid-like appearance while avoiding the harshness of sharp corners.

## Components

### Buttons
Primary buttons use a solid Slate Teal. Secondary buttons use the frosted glass effect with a subtle border. Ghost buttons are reserved for tertiary actions or "Cancel" functions to keep the UI clean.

### Shift Cards
The core component of the system. These should be semi-transparent with a 1px border. Status is indicated by a vertical bar on the left edge (e.g., Green for "Filled", Amber for "Pending") rather than coloring the entire card, which would break the glass aesthetic.

### Input Fields
Inputs are minimalist: a soft grey bottom border that transitions to a Slate Teal border on focus. Backgrounds should be slightly more opaque than the surrounding glass panel to indicate interactivity.

### Chips & Badges
Used for employee tags or shift roles. These should be pill-shaped with low-saturation background tints and high-contrast text.

### Navigation Sidebar
A vertical glass panel on the far left. Active states are indicated by a subtle glow behind the icon and a font-weight increase, avoiding heavy background blocks.

### Modals
Large-scale glass overlays with a backdrop-filter that blurs the entire workspace behind it, forcing focus on the management task at hand.