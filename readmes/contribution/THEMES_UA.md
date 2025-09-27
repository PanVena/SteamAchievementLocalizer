# Інструкція по додаванню нових тем

**🇺🇸 [English version / Англійська версія](THEMES.md)**

## Як додати нову тему

### Крок 1: Створити JSON файл теми

Створіть новий файл у папці `assets/themes/` з назвою `назва_теми.json`.

Структура файлу:
```json
{
  "name": "НазваТеми",               // Назва теми (як буде збережено в налаштуваннях)
  "display_name": "display",         // Ключ для локалізації (theme_display у lang файлах)
  "style": "Fusion",                 // Qt стиль: "Fusion", "system" або інший
  "palette": {                       // Палітра кольорів
    "window": [R, G, B],             // RGB або "white"/"red" тощо
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
  "styles": {                        // CSS стилі для віджетів
    "QLabel": "color: #000;",
    "QLineEdit": "color: #000; background: #fff;",
    "QGroupBox": "QGroupBox { font-weight: bold; }",
    "QPushButton": "QPushButton { ... }"
  }
}
```

### Крок 2: Додати тему до порядку (опціонально)

Якщо хочете, щоб тема з'являлася у певному місці меню, відредагуйте файл `assets/plugins/theme_manager.py`:

```python
self.theme_order = [
    "System",
    "Dark", 
    "Light",
    "ВашаНоваТема",  # Додайте сюди
    "Femboy",
    "Blue"
]
```

### Крок 3: Додати локалізацію (опціонально)

У файлах `assets/locales/lang_*.json` додайте переклад:

```json
{
  "theme_вашаназва": "Назва Вашої Теми"
}
```

## Існуючі теми

- **System** - використовує системну тему
- **Dark** - темна тема з високим контрастом  
- **Light** - світла тема
- **Femboy** - рожево-фіолетова тема

## Корисні поради

1. **RGB кольори**: `[255, 0, 0]` для червоного
2. **Іменовані кольори**: `"white"`, `"black"`, `"red"` тощо
3. **Системна тема**: використовуйте `"palette": "system"` для системних кольорів
4. **CSS стилі**: підтримуються всі Qt CSS властивості
5. **Тестування**: нова тема автоматично з'явиться в меню після перезапуску

## Приклад повної теми

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

## Технічні деталі

### Підтримувані властивості палітри

- `window` - основний фон вікна
- `window_text` - текст на фоні вікна
- `base` - фон полів вводу
- `alternate_base` - альтернативний фон (для рядків таблиць)
- `tooltip_base` - фон підказок
- `tooltip_text` - текст підказок
- `text` - основний колір тексту
- `button` - фон кнопок
- `button_text` - текст на кнопках
- `bright_text` - яскравий текст (для виділень)
- `link` - колір посилань
- `highlight` - колір виділення
- `highlighted_text` - текст на виділеному фоні

### Підтримувані Qt стилі

- `QLabel` - мітки тексту
- `QLineEdit` - поля вводу
- `QGroupBox` - групи елементів
- `QPushButton` - кнопки
- `QComboBox` - випадаючі списки
- `QTableWidget` - таблиці
- `QCheckBox` - прапорці

### Псевдо-стани для кнопок

- `:hover` - при наведенні миші
- `:pressed` - при натисканні
- `:checked` - для прапорців та перемикачів
- `:disabled` - для заблокованих елементів

## Приклади кольорових схем

### Темна синя тема
```json
{
  "name": "DarkBlue",
  "palette": {
    "window": [25, 35, 45],
    "window_text": [200, 200, 200],
    "base": [35, 45, 55],
    "button": [45, 55, 65],
    "highlight": [70, 130, 180]
  }
}
```

### Тепла помаранчева тема
```json
{
  "name": "WarmOrange",
  "palette": {
    "window": [255, 248, 240],
    "window_text": [139, 69, 19],
    "base": [255, 250, 240],
    "button": [255, 228, 196],
    "highlight": [255, 140, 0]
  }
}
```

### Мінімалістична сіра тема
```json
{
  "name": "Minimal",
  "palette": {
    "window": [248, 248, 248],
    "window_text": [64, 64, 64],
    "base": [255, 255, 255],
    "button": [240, 240, 240],
    "highlight": [100, 100, 100]
  }
}
```

## Налагодження тем

Якщо тема не завантажується:

1. **Перевірте синтаксис JSON** - використовуйте валідатор JSON
2. **Перевірте назву файлу** - має закінчуватись на `.json`
3. **Перевірте структуру** - всі обов'язкові поля мають бути присутні
4. **Перезапустіть програму** - теми завантажуються при старті
5. **Перевірте консоль** - помилки виводяться в консоль

## Поділитися темою

Якщо ви створили гарну тему, поділіться нею з іншими:

1. Створіть Issue на GitHub з темою
2. Опишіть особливості вашої теми
3. Додайте скріншоти
4. Приєднайте JSON файл теми

Ваша тема може бути включена в наступну версію програми!