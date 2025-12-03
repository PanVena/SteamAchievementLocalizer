# Інструкції зі збірки для Windows

## Проблема з темами
При компіляції програми у виконуваний файл (.exe) для Windows, теми можуть не працювати, якщо папка `assets/themes` не включена до збірки.

## Рішення

### Варіант 1: Nuitka (рекомендовано)

```bash
python -m nuitka --standalone --onefile \
  --enable-plugin=pyqt6 \
  --include-data-dir=assets=assets \
  --windows-icon-from-ico=assets/icon.ico \
  --product-name="Steam Achievement Localizer" \
  --file-version="0.8.1" \
  --product-version="0.8.1" \
  --company-name="Vena" \
  --file-description="Steam Achievement Localizer" \
  SteamAchievementLocalizer.py
```

Важливо: опція `--include-data-dir=assets=assets` включає всю папку `assets` (включаючи теми, локалі, іконки) до виконуваного файлу.

### Варіант 2: PyInstaller

Створіть файл `SteamAchievementLocalizer.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['SteamAchievementLocalizer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Включаємо всю папку assets
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SteamAchievementLocalizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
```

Потім запустіть:

```bash
pyinstaller SteamAchievementLocalizer.spec
```

### Варіант 3: Ручне копіювання (для тестування)

Якщо ви не хочете перекомпілювати програму, можете просто скопіювати папку `assets` поруч з виконуваним файлом:

```
SteamAchievementLocalizer.exe
assets/
  themes/
    catppuccin_mocha.json
    dark.json
    darkfemboy.json
    femboy.json
    light.json
    system.json
  locales/
    ...
  icon.ico
  steam.api.allgamenames.json
```

## Перевірка

Після збірки переконайтеся, що:
1. Програма запускається без помилок
2. У меню Settings -> Theme всі теми доступні
3. Зміна теми застосовується коректно
4. Теми зберігаються при перезапуску програми

## Зміни в коді

Код уже виправлено для підтримки обох режимів (розробка та збірка):
- У `theme_manager.py` додано метод `_get_resource_path()` для правильного визначення шляхів
- Шлях до тем тепер визначається автоматично залежно від режиму запуску
