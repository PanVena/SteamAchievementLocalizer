def replace_all_columns_in_bin(headers, table, steam_folder, game_id):
    

    import re

    # Збираємо всі дані таблиці
    headers = self.headers  # ['key', 'english', 'ukrainian', ...]
    key_col = 0  # припускаємо, що перша колонка — ключ

    # Створюємо словник: {key: {lang1: value1, lang2: value2, ...}}
    data_by_key = {}
    for row_i in range(self.table.rowCount()):
        row = {}
        for col_i, col_name in enumerate(headers):
            item = self.table.item(row_i, col_i)
            row[col_name] = item.text() if item else ''
        key = row[headers[key_col]]
        if key:
            data_by_key[key] = row

    # Шлях до вхідного бінарного файлу
    file_path = f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{self.game_id()}.bin"

    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        QMessageBox.warning(self, "Помилка", f"Файл не знайдено: {file_path}")
        return

    # Функції для пошуку ключа та заміни тексту у бінарних даних
    def replace_text_in_chunk(chunk, translations_row):
        """
        Замінює всі рядки з таблиці у цьому шматку chunk.
        translations_row — dict з {col_name: value}
        """
        # Знаходимо всі текстові підрядки, які можна замінити
        for lang in headers[1:]:
            value = translations_row.get(lang, '')
            if not value:
                continue
            # Пошук підрядка (англійський текст у оригіналі)
            # Припускаємо, що текст зберігається у вигляді b'\x01' + bytes(text, 'utf8') + b'\x00'
            # Знаходимо старе значення (старий текст) для цього lang
            pattern = re.compile(b'\x01' + lang.encode('utf8') + b'\x00(.*?)\x00', re.DOTALL)
            m = pattern.search(chunk)
            if m:
                old_bytes = m.group(1)
                # Замінюємо старе значення на нове (у байтах)
                new_chunk = chunk[:m.start(1)] + value.encode('utf8') + chunk[m.end(1):]
                chunk = new_chunk
        return chunk

    # Розбиваємо файл на "чанки" (кожен chunk — один запис/achievement)
    def split_chunks(data: bytes):
        pattern = re.compile(b'\x00bits\x00|\x02bit\x00')
        positions = [m.start() for m in pattern.finditer(data)]
        chunks = []
        for i in range(len(positions)):
            start = positions[i]
            end = positions[i + 1] if i + 1 < len(positions) else len(data)
            chunks.append(data[start:end])
        return chunks

    def extract_key_and_data(chunk: bytes):
        key_pattern = re.compile(b'\x00\x01name\x00(.*?)\x00', re.DOTALL)
        key_match = key_pattern.search(chunk)
        if key_match:
            return key_match.group(1).decode(errors='ignore')
        return None

    # Розбиваємо на чанки
    chunks = split_chunks(data)
    new_chunks = []
    for chunk in chunks:
        key = extract_key_and_data(chunk)
        if key and key in data_by_key:
            new_chunk = replace_text_in_chunk(chunk, data_by_key[key])
            new_chunks.append(new_chunk)
        else:
            new_chunks.append(chunk)

    # Склеюємо назад і записуємо
    updated_data = b''.join(new_chunks)
    try:
        with open(file_path, "wb") as f:
            f.write(updated_data)
        QMessageBox.information(self, "Успіх", "Всі локалізації збережено у .bin-файл.")
    except Exception as e:
        QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти .bin:\n{e}")
    
    return updated_data 