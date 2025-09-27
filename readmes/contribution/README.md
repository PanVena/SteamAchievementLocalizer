# Contribution Documentation

This folder contains documentation for contributors and developers.

## Theme Development

- **[THEMES.md](THEMES.md)** - Complete theme creation guide in English
- **[THEMES_UA.md](THEMES_UA.md)** - Повний посібник зі створення тем українською мовою

## Localization

- **[LOCALES.md](LOCALES.md)** - Language addition guide in English  
- **[LOCALES_UA.md](LOCALES_UA.md)** - Посібник з додавання мов українською мовою

## Adding New Documentation

When adding new contribution documentation:

1. Place files in this `readmes/contribution/` folder
2. Update links in all main README files:
   - `/README.md` (main English README)
   - `/readmes/README.uk.md` (Ukrainian README)  
   - `/readmes/README.pl.md` (Polish README)
3. Add cross-references between related documentation
4. Update table of contents in README files

## Structure

```
readmes/
├── contribution/          # Developer and contributor documentation
│   ├── README.md         # This file
│   ├── THEMES.md         # Theme creation guide (English)
│   └── THEMES_UA.md      # Theme creation guide (Ukrainian)
├── screens/              # Screenshots for README files
├── README.uk.md          # Ukrainian README
└── README.pl.md          # Polish README
```