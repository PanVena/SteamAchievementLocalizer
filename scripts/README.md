# Build Scripts

Ця папка містить скрипти для компіляції програми.

## Скрипти

### build_windows.bat / build_windows.sh
Автоматична збірка програми для Windows з використанням Nuitka.

**Використання (Windows):**
```cmd
scripts\build_windows.bat
```

**Використання (Linux/Mac для крос-компіляції):**
```bash
chmod +x scripts/build_windows.sh
./scripts/build_windows.sh
```

**Що робить:**
- Автоматично визначає версію програми з `SteamAchievementLocalizer.py`
- Компілює програму в один виконуваний файл
- Включає всю папку `assets` (теми, локалізації, іконки)
- Створює Windows-виконуваний файл без консолі

### bump_version.py
Скрипт для автоматичного оновлення версії в усіх файлах проєкту.

## Вимоги

Для збірки потрібно встановити:

```bash
pip install nuitka
pip install PyQt6
```

Або для PyInstaller:
```bash
pip install pyinstaller
```

## Альтернатива: PyInstaller

Якщо ви воліте використовувати PyInstaller замість Nuitka:

```bash
pyinstaller SteamAchievementLocalizer.spec
```

Результат буде в папці `dist/`.

## Важливо

Переконайтеся, що при збірці включена папка `assets`:
- `assets/themes/` - файли тем
- `assets/locales/` - файли локалізацій
- `assets/icon.ico` - іконка програми
- `assets/steam.api.allgamenames.json` - база даних ігор

Без цих файлів деякі функції програми не працюватимуть!
