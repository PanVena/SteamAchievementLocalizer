# Theme Addition Instructions

**🇺🇦 [Українська версія / Ukrainian version](THEMES_UA.md)**

## How to add new themes

### Step 1: Create theme JSON file

Create a new file in the `assets/themes/` folder named `theme_name.json`.

File structure:
```json
{
  "name": "ThemeName",               // Theme name (how it will be saved in settings)
  "display_name": "display",         // Key for localization (theme_display in lang files)
  "style": "Fusion",                 // Qt style: "Fusion", "system" or other
  "palette": {                       // Color palette
    "window": [R, G, B],             // RGB or "white"/"red" etc
    "window_text": [R, G, B],
    "base": [R, G, B],
    "alternate_base": [R, G, B],
    "tooltip_base": [R, G, B],
    "tooltip_text": [R, G, B],
    "text": [R, G, B],
    "button": [R, G, B],
    "button_text": [R, G, B],
    "bright_text": [R, G, B],
    "link": [R, G, B],
    "highlight": [R, G, B],
    "highlighted_text": [R, G, B]
  },
  "styles": {                        // CSS styles for widgets
    "QLabel": "color: #000;",
    "QLineEdit": "color: #000; background: #fff;",
    "QGroupBox": "QGroupBox { font-weight: bold; }",
    "QPushButton": "QPushButton { ... }"
  }
}
```

### Step 2: Add theme to order (optional)

If you want the theme to appear in a specific place in the menu, edit the file `assets/plugins/theme_manager.py`:

```python
self.theme_order = [
    "System",
    "Dark", 
    "Light",
    "YourNewTheme",  # Add here
    "Femboy",
    "Blue"
]
```

### Step 3: Add localization (optional)

In the files `assets/locales/lang_*.json` add translation:

```json
{
  "theme_yourname": "Your Theme Name"
}
```

## Existing themes

- **System** - uses system theme
- **Dark** - dark theme with high contrast  
- **Light** - light theme
- **Femboy** - pink-purple theme

## Useful tips

1. **RGB colors**: `[255, 0, 0]` for red
2. **Named colors**: `"white"`, `"black"`, `"red"` etc
3. **System theme**: use `"palette": "system"` for system colors
4. **CSS styles**: all Qt CSS properties are supported
5. **Testing**: new theme will automatically appear in menu after restart

## Complete theme example

```json
{
  "name": "Green",
  "display_name": "green", 
  "style": "Fusion",
  "palette": {
    "window": [240, 255, 240],
    "window_text": [0, 100, 0],
    "base": [245, 255, 245],
    "alternate_base": [230, 250, 230],
    "tooltip_base": [200, 255, 200],
    "tooltip_text": [0, 0, 0],
    "text": [0, 100, 0],
    "button": [180, 255, 180],
    "button_text": [0, 100, 0],
    "bright_text": [255, 0, 0],
    "link": [0, 0, 255],
    "highlight": [0, 255, 0],
    "highlighted_text": "white"
  },
  "styles": {
    "QLabel": "color: #006400;",
    "QLineEdit": "color: #006400; background-color: #F5FFF5; border: 1px solid #228B22; padding: 2px;",
    "QGroupBox": "QGroupBox { color: #006400; font-weight: bold; }",
    "QPushButton": "QPushButton { background-color: #B4FFB4; color: #006400; border: 2px solid #228B22; border-radius: 4px; padding: 4px; font-weight: bold; } QPushButton:hover { background-color: #90EE90; } QPushButton:pressed { background-color: #32CD32; }"
  }
}
```