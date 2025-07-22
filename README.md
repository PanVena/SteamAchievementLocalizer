
<h1>🏆 Steam Achievement Localizer від Вени</h1>

<p><strong>Steam Achievement Localizer</strong> — це 💻 настільний застосунок на <strong>Python + PyQt6</strong>, який дозволяє легко <strong>переглядати</strong>, <strong>експортувати</strong>, <strong>перекладати</strong> та <strong>редагувати досягнення</strong> у <code>.bin</code> файлах Steam. Працює навіть з «досягненнями для ледачих» 👀</p>

<p><a class="button-link" href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest" target="_blank">👉 Завантажити останню версію 👈</a></p>

<h2>💡 Основні можливості</h2>
<ul>
    <li>📂 Читання <code>.bin</code> файлів Steam (<code>UserGameStatsSchema_XXXX.bin</code>)</li>
    <li>📊 Зручне представлення досягнень у таблиці</li>
    <li>🧾 Експорт в <strong>CSV</strong> з підтримкою <strong>контексту</strong></li>
    <li>🌐 Імпорт власних перекладів із CSV назад у <code>.bin</code></li>
    <li>🌍 Підтримка <strong>багатьох мов</strong>, зокрема <code>ukrainian</code></li>
    <li>🤖 Інтерфейс українською мовою з душевним гумором</li>
    <li>🧠 Підсвічування результатів пошуку</li>
    <li>🔎 Автоматичне визначення шляху до Steam</li>
    <li>🔐 Безпечне редагування — лише потрібні поля, усе інше зберігається</li>
</ul>

<h2>📋 Як користуватись</h2>
<ol>
    <li>Запусти програму</li>
    <li>Автоматично обрати теку Steam (або залишити стандартну: <code>C:\Program Files (x86)\Steam</code>)</li>
    <li>Введи ID гри або посилання з крамниці Steam</li>
    <li>Натисни "Шукай ачівки"!</li>
    <li>Переглянь таблицю з досягненнями</li>
    <li>Вибери мову з переліку</li>
    <li>Натисни «Експорт CSV» </li>
    <li>У CSV-файлі заповни колонку <code>ukrainian</code> своїм перекладом</li>
    <li>Імпортуй файл назад</li>
    <li>Натисни «Зберегти бінарник», щоб замінити файл Steam або зберегти копію для себе</li>
</ol>

<p><strong>🧯 У разі помилок — видали файл отут і перезапусти стім і зайшовши на сторінку гри у бібліотеці:</strong><br>
<code>C:\Program Files (x86)\Steam\appcache\stats\UserGameStatsSchema_XXXX.bin</code><br>
<strong>Або знайшовши його у природному середовищі)</strong></p>

<h2>✏️ Структура CSV-файлу</h2>

<table>
    <thead>
        <tr>
            <th>key</th>
            <th>english</th>
            <th>ukrainian</th>
            <th>context_column (будь-яка)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>NAME_ACHIEVE</td>
            <td>First Step</td>
            <td>Перший крок</td>
            <td>Pierwszy krok</td>
        </tr>
    </tbody>
</table>


<h2>📦 Встановлення (для розробників)</h2>
<pre><code>git clone https://github.com/PanVena/SteamAchievementLocalizer.git
cd SteamAchievementLocalizer
pip install -r requirements.txt
python SteamAchievementLocalizer.py
</code></pre>
<p><strong>Потрібно:</strong> Python 3.10+, PyQt6, csv, re</p>

<h2>👥 Спільнота</h2>
<p>Приєднуйтесь до спілки перекладачів:<br>
<a href="https://t.me/linyvi_sh_ji" target="_blank">👉 Телеграм-канал "Ліниві ШІ"</a></p>

<h2>💰 Подякувати</h2>
<p>Якщо софт зекономив тобі час і нерви — можеш «перекинути кілька біткоїнів гривнею» 😄<br>
<a href="https://send.monobank.ua/jar/47ipoRVJAk" target="_blank">➡ ТУТ 🌻 Mono Jar</a></p>

<h2>🛠 Технічні деталі</h2>
<ul>
    <li>Працює з <code>UserGameStatsSchema_XXXX.bin</code> файлами Steam</li>
    <li>Текст витягується через патерни <code>\x01{language}\x00{text}\x00</code></li>
    <li>Автоматично додається <code>ukrainian</code>, якщо його нема</li>
    <li>Редагуються лише необхідні мови, решта байтів залишаються недоторканими</li>
</ul>

<h2>🔖 Ліцензія</h2>
<p>MIT — користуйся, змінюй, перекладай, зберігай, радій.</p>

<h2>🧑‍💻 Автор</h2>
<p><strong>Вена</strong><br>
<a href="https://github.com/PanVena" target="_blank">GitHub</a> | <a href="https://t.me/Pan_Vena" target="_blank">Telegram</a></p>

<blockquote>
    <p><strong><i>У посібничках до українізаторів кажемо, що файлик кидать до "C:\Program Files (x86)\Steam\appcache\stats\", з заміною.</i></strong></p>
</blockquote>
