# Locale Addition Instructions

**🇺🇦 [Українська версія / Ukrainian version](LOCALES_UA.md)**

## How to add new languages

### Step 1: Create locale JSON file

Create a new file in the `assets/locales/` folder named `lang_[code].json` (e.g., `lang_de.json`).

File structure:
```json
{
  "_locale_info": {
    "name": "Deutsch",
    "native_name": "Deutsch (German)",  
    "code": "de",
    "priority": 50
  },
  "app_title": "Steam Achievement Localizer by Pan_Vena ver ",
  "warning_title_achtung": "Achtung",
  "warning_message": "...",
  "man_select_file_label": "...",
  "man_select_file": "...",
  "get_ach": "...",
  // ... all other translation keys
}
```

### Required metadata fields:

- **name**: Internal language identifier (used in settings)
- **native_name**: Display name in menu (with English name in parentheses)
- **code**: Language code (ISO 639-1 preferred)
- **priority**: Menu sort order (lower = higher in menu, default=999)

### Step 2: No code editing needed!

The locale will automatically appear in the Language menu after program restart.
The system will:
- Automatically scan the `assets/locales/` directory
- Sort languages by priority then alphabetically
- Use native names from `_locale_info` 
- Fall back to filename if metadata is missing

### Existing locales:

- **English** (priority: 10) - `lang_en.json`
- **Українська** (priority: 20) - `lang_ua.json` 
- **Polski** (priority: 30) - `lang_pl.json`

### Translation keys:

Copy all keys from existing locale files. The most complete one is usually `lang_en.json`.
Missing keys will fall back to English translations.

### Testing:

1. Add your JSON file to `assets/locales/`
2. Restart the application
3. Your language should appear in Language menu, sorted by priority
4. Test switching to it to verify all translations work

### Example minimal locale:

```json
{
  "_locale_info": {
    "name": "Español",
    "native_name": "Español (Spanish)",
    "code": "es", 
    "priority": 40
  },
  "app_title": "Localizador de Logros de Steam por Pan_Vena ver ",
  "language": "Idioma",
  "appearance": "Apariencia"
}
```

New languages will be automatically discovered and added to the interface!