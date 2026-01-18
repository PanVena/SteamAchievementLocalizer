#!/bin/bash
set -e  # Зупинитися при помилці

echo "=========================================="
echo "Локальна збірка AppImage для Linux"
echo "=========================================="

# Кольори для виводу
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Перевірка версії
echo -e "${YELLOW}Перевірка версії...${NC}"
APP_VERSION=$(grep -oP 'APP_VERSION *= *"\K[0-9]+\.[0-9]+\.[0-9]+' SteamAchievementLocalizer.py)
if [ -z "$APP_VERSION" ]; then
    echo -e "${RED}Помилка: не вдалося знайти APP_VERSION у SteamAchievementLocalizer.py${NC}"
    exit 1
fi
echo -e "${GREEN}Версія додатку: $APP_VERSION${NC}"

# Очищення попередніх збірок
echo -e "${YELLOW}Очищення попередніх збірок...${NC}"
rm -rf dist build *.build SteamAchievementLocalizer.AppDir

# Компіляція з Nuitka
echo -e "${YELLOW}Компіляція з Nuitka...${NC}"
python3.12 -m nuitka SteamAchievementLocalizer.py --standalone \
    --remove-output \
    --output-dir=dist \
    --plugin-enable=pyqt6 \
    --include-data-dir=assets=assets \
    --include-package=certifi \
    --include-package-data=certifi \
    --include-package=requests \
    --include-package=urllib3 \
    --include-module=plugins.http_client \
    --assume-yes-for-downloads \
    --show-progress

echo -e "${GREEN}Компіляція завершена!${NC}"
echo "Вміст dist/:"
ls -la dist/

# Знайти директорію Nuitka
echo -e "${YELLOW}Пошук директорії Nuitka...${NC}"
nuitka_dir=$(find dist -maxdepth 1 -type d -name "SteamAchievementLocalizer*" | head -n1)
if [ -z "$nuitka_dir" ]; then
    echo -e "${RED}Помилка: не знайдено директорію Nuitka${NC}"
    exit 1
fi
echo -e "${GREEN}Знайдено: $nuitka_dir${NC}"

# Створення структури AppDir
echo -e "${YELLOW}Створення структури AppDir...${NC}"
appdir="SteamAchievementLocalizer.AppDir"
mkdir -p "$appdir/usr/bin"
mkdir -p "$appdir/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$appdir/usr/share/applications"

# Копіювання файлів з Nuitka до AppDir
echo -e "${YELLOW}Копіювання файлів...${NC}"
cp -r "$nuitka_dir"/* "$appdir/usr/bin/"

# Знайти виконуваний файл
exe_file=$(find "$appdir/usr/bin" -maxdepth 1 -name "SteamAchievementLocalizer*" -type f -executable | head -n1)
exe_name=$(basename "$exe_file")
echo -e "${GREEN}Знайдено виконуваний файл: $exe_name${NC}"

# Конвертація іконки
echo -e "${YELLOW}Конвертація іконки...${NC}"
if [ -f "assets/icon.ico" ]; then
    # Перевірка наявності ImageMagick
    if ! command -v convert &> /dev/null; then
        echo -e "${RED}Помилка: ImageMagick не встановлено. Встановіть: sudo dnf install ImageMagick${NC}"
        exit 1
    fi
    
    convert "assets/icon.ico[4]" "$appdir/steamachievementlocalizer.png"
    convert "assets/icon.ico[4]" "$appdir/usr/share/icons/hicolor/256x256/apps/steamachievementlocalizer.png"
    echo -e "${GREEN}Іконка сконвертована успішно${NC}"
else
    echo -e "${RED}Помилка: assets/icon.ico не знайдено${NC}"
    exit 1
fi

# Створення .desktop файлу
echo -e "${YELLOW}Створення .desktop файлу...${NC}"
cat > "$appdir/steamachievementlocalizer.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=Steam Achievement Localizer
GenericName=Achievement Localizer
Comment=Localize Steam achievement files
Exec=SteamAchievementLocalizer
Icon=steamachievementlocalizer
Categories=Utility;Game;
Terminal=false
StartupNotify=true
Keywords=steam;achievements;localization;translation;
MimeType=application/octet-stream;
X-AppImage-Version=$APP_VERSION
X-AppImage-Author=Pan Vena
X-AppImage-License=MIT
X-AppImage-URL=https://github.com/PanVena/SteamAchievementLocalizer
DESKTOP_EOF

# Замінити змінну версії
sed -i "s/\$APP_VERSION/$APP_VERSION/" "$appdir/steamachievementlocalizer.desktop"

cp "$appdir/steamachievementlocalizer.desktop" "$appdir/usr/share/applications/"
echo -e "${GREEN}.desktop файл створено${NC}"

# Створення AppRun скрипту
echo -e "${YELLOW}Створення AppRun скрипту...${NC}"
cat > "$appdir/AppRun" << APPRUN_EOF
#!/bin/bash
SELF=\$(readlink -f "\$0")
HERE=\${SELF%/*}
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/bin:\${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="\${HERE}/usr/bin"
cd "\${HERE}/usr/bin"
exec "\${HERE}/usr/bin/$exe_name" "\$@"
APPRUN_EOF

chmod +x "$appdir/AppRun"
echo -e "${GREEN}AppRun створено${NC}"

# Завантаження appimagetool якщо потрібно
echo -e "${YELLOW}Перевірка appimagetool...${NC}"
if [ ! -f "appimagetool" ]; then
    echo -e "${YELLOW}Завантаження appimagetool...${NC}"
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O appimagetool
    chmod +x appimagetool
    echo -e "${GREEN}appimagetool завантажено${NC}"
else
    echo -e "${GREEN}appimagetool вже існує${NC}"
fi

# Створення AppImage
echo -e "${YELLOW}Створення AppImage...${NC}"
appimage_name="SteamAchievementLocalizer-linux64.AppImage"

# Спроба створити AppImage (з fallback для FUSE)
if ARCH=x86_64 ./appimagetool "$appdir" "$appimage_name" 2>/dev/null; then
    echo -e "${GREEN}AppImage створено (нативний режим)${NC}"
else
    echo -e "${YELLOW}Нативний режим не вдався, використовую --appimage-extract-and-run...${NC}"
    ARCH=x86_64 ./appimagetool --appimage-extract-and-run "$appdir" "$appimage_name"
    echo -e "${GREEN}AppImage створено (extract-and-run режим)${NC}"
fi

chmod +x "$appimage_name"

echo ""
echo -e "${GREEN}=========================================="
echo "Збірка завершена успішно!"
echo "==========================================${NC}"
echo -e "AppImage: ${YELLOW}$appimage_name${NC}"
echo -e "Версія: ${YELLOW}$APP_VERSION${NC}"
ls -lh "$appimage_name"
echo ""
echo -e "${GREEN}Запустіть AppImage командою:${NC}"
echo -e "${YELLOW}./$appimage_name${NC}"
