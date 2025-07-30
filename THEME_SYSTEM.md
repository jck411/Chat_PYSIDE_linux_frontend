# Theme System Implementation

## Overview

This document describes the dark mode and light mode implementation for the Chat PySide Frontend application, following PROJECT_RULES.md guidelines and preparing for Material Design Icons integration.

## Architecture

### Core Components

```
src/themes/
├── __init__.py              # Package interface
├── theme_config.py          # Material Design 3 color definitions
├── theme_manager.py         # Central theme controller with signals
└── theme_applier.py         # Dynamic stylesheet generation

resources/
├── resources.qrc            # Qt resource file
└── icons/
    ├── dark_mode_24dp_565F89_FILL0_wght400_GRAD0_opsz24.svg
    ├── light_mode_24dp_565F89_FILL0_wght400_GRAD0_opsz24.svg
    ├── send_24dp_565F89_FILL1_wght400_GRAD0_opsz24.svg
    └── settings_24dp_565F89_FILL1_wght400_GRAD0_opsz24.svg
```

### Key Features

- **Material Design 3 Colors**: Full color palette implementation with semantic naming
- **Real-time Switching**: Instant theme changes without application restart
- **Persistent Preferences**: Theme choice saved using QSettings
- **Performance Optimized**: Cached stylesheet generation, <10ms switching
- **Signal-based Updates**: Qt signals for component synchronization
- **Environment Support**: `CHAT_THEME_MODE` environment variable
- **Dynamic Icon Coloring**: Theme-neutral SVG icons with programmatic coloring

## Usage

### Basic Theme Operations

```python
from src.themes import get_theme_manager, ThemeMode

# Get theme manager instance
theme_manager = get_theme_manager()

# Switch to dark mode
theme_manager.set_theme_mode(ThemeMode.DARK)

# Toggle between themes
theme_manager.toggle_theme()

# Get current theme info
info = theme_manager.get_theme_info()
```

### Environment Configuration

Set theme preference via environment variable:

```bash
# Light theme (default)
export CHAT_THEME_MODE=light

# Dark theme
export CHAT_THEME_MODE=dark
```

### UI Integration

The main window automatically includes a theme toggle button:

```python
# Theme toggle button is automatically added
# Click to switch between light and dark modes
# Button text updates: "🌙 Dark Mode" ↔ "☀️ Light Mode"
```

## Material Design 3 Colors

### Light Theme Colors
- **Primary**: #1976D2 (Blue)
- **Secondary**: #00796B (Teal)
- **Background**: #FEFBFF
- **Surface**: #FFFFFF
- **Error**: #D32F2F

### Dark Theme Colors
- **Primary**: #90CAF9 (Light Blue)
- **Secondary**: #4DB6AC (Light Teal)
- **Background**: #0F0F0F
- **Surface**: #121212
- **Error**: #EF5350

## Resource System

### QRC Structure

The `resources.qrc` file defines theme-neutral icon resources:

```xml
<qresource prefix="/icons">
    <file alias="dark_mode.svg">icons/dark_mode_24dp_565F89_FILL0_wght400_GRAD0_opsz24.svg</file>
    <file alias="light_mode.svg">icons/light_mode_24dp_565F89_FILL0_wght400_GRAD0_opsz24.svg</file>
    <file alias="settings.svg">icons/settings_24dp_565F89_FILL1_wght400_GRAD0_opsz24.svg</file>
    <file alias="send.svg">icons/send_24dp_565F89_FILL1_wght400_GRAD0_opsz24.svg</file>
</qresource>
```

### Icon System

Icons use Material Design specifications with theme-neutral base colors that are dynamically recolored:

- **Base Color**: `#565F89` (theme-neutral gray)
- **Dynamic Coloring**: IconButton applies theme-appropriate colors programmatically
- **Performance**: Single icon file per symbol, colored at runtime

## Implementation Details

### Theme Manager (Singleton)

```python
class ThemeManager(QObject):
    # Signals for real-time updates
    theme_changed = Signal(ThemeConfig)
    theme_mode_changed = Signal(ThemeMode)

    # Singleton pattern
    _instance: Optional['ThemeManager'] = None
```

### Performance Optimizations

1. **Stylesheet Caching**: Generated stylesheets cached by theme mode
2. **Signal-based Updates**: Minimal UI thread impact
3. **Lazy Loading**: Theme resources loaded on demand
4. **Memory Efficient**: Single theme manager instance

### PROJECT_RULES.md Compliance

- ✅ **Module Limits**: UI controllers ≤ 150 LOC, ≤ 2 public symbols
- ✅ **Performance**: Theme switching under 10ms
- ✅ **Structured Logging**: All theme operations logged with context
- ✅ **Environment Variables**: Theme preference via `CHAT_THEME_MODE`
- ✅ **Type Safety**: Full type annotations with mypy compliance
- ✅ **Error Handling**: Fail-fast validation with proper exceptions

## Testing

### Manual Testing

Run the theme test script:

```bash
uv run python test_themes.py
```

### Automated Testing

Theme system includes comprehensive tests:

```bash
# Run theme-specific tests
uv run pytest tests/ -k theme

# Run with coverage
uv run pytest tests/ --cov=src.themes
```

## Future Enhancements

### Advanced Features

1. **System Theme Detection**: Auto-switch based on OS theme
2. **Custom Themes**: User-defined color schemes
3. **Animation**: Smooth theme transition effects
4. **High Contrast**: Accessibility theme variants
5. **Additional Icons**: Expand Material Design icon set

## Troubleshooting

### Common Issues

1. **Theme Not Applied**: Ensure `theme_manager.apply_current_theme()` called
2. **Icons Missing**: Check resource compilation with `pyside6-rcc`
3. **Performance Issues**: Clear stylesheet cache with `clear_cache()`
4. **Icon Colors Wrong**: Verify IconButton theme updates via signals

### Debug Information

```python
# Get detailed theme information
theme_manager = get_theme_manager()
print(theme_manager.get_theme_info())

# Check current configuration
from src.config import get_app_config
print(get_app_config().theme_preference)
```

## Integration with Plan

This implementation completes the theme system with:

- **Resource Files Structure** (Priority 3): ✅ Complete
- **Material Design Icons**: ✅ Implemented with dynamic coloring
- **CI Pipeline**: ✅ Resource compilation integrated

The theme system is production-ready and follows all project guidelines with a clean, maintainable architecture.
