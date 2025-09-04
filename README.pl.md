[![uk](https://img.shields.io/badge/українська-blue.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.uk.md)
[![en](https://img.shields.io/badge/english-red.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.md)



<h1>🏆 Lokalizator osiągnięć Steam od Veny</h1>



<p><strong>Steam Achievement Localizer</strong> to narzędzie GUI oparte na PyQt6 do edycji plików osiągnięć Steam (UserGameStatsSchema\_xxx.bin).

Pozwala tłumaczyć i lokalizować opisy osiągnięć oraz zapisywać zmiany bezpośrednio w folderze Steam lub jako osobny plik.</p>



<p><a class="button-link" href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest" target="\_blank">👉 Pobierz najnowszą wersję 👈</a></p>



!\[Screenshot](assets/scrn\_en.png)



\## 📌 Funkcje

\- Automatyczne wykrywanie folderu Steam (przez Rejestr Windows).

\- Ładowanie pliku `UserGameStatsSchema\_\*.bin`:

&nbsp; - ręcznie,

&nbsp; - lub automatycznie według ID gry.

\- Podgląd i edycja tabeli osiągnięć.

\- Wyszukiwanie według kolumny.

\- Eksport do CSV:

&nbsp; - wszystkie języki naraz,

&nbsp; - specjalny format do tłumaczenia.

\- Import tłumaczeń z CSV z powrotem do aplikacji.

\- Automatyczne wsparcie dla języka ukraińskiego (dodaje kolumnę, jeśli jej brakuje).

\- Podmiana tłumaczeń bezpośrednio w plikach `.bin`.

\- Zapis:

&nbsp; - bezpośrednio do folderu Steam,

&nbsp; - lub w dowolne miejsce.

\- Wielojęzyczny interfejs (angielski, ukraiński).



<blockquote>

&nbsp;  <h2> <p><strong><i>W przewodnikach dla tłumaczy zalecamy umieszczenie pliku w „C:\\Program Files (x86)\\Steam\\appcache\\stats\\”, zastępując oryginał.</i></strong></p></h2>

</blockquote>



<p><strong>🧯 Jeśli napotkasz błędy — usuń plik tutaj, zrestartuj Steam i wejdź na stronę gry w swojej bibliotece:</strong><br>

<code>C:\\Program Files (x86)\\Steam\\appcache\\stats\\UserGameStatsSchema\_XXXX.bin</code><br>

<strong>Lub znajdź go w jego naturalnym środowisku :)</strong></p>



<h2>✏️ Struktura pliku CSV</h2>



<table>

&nbsp;   <thead>

&nbsp;       <tr>

&nbsp;           <th>key</th>

&nbsp;           <th>english</th>

&nbsp;           <th>ukrainian</th>

&nbsp;           <th>context\_column (dowolny)</th>

&nbsp;       </tr>

&nbsp;   </thead>

&nbsp;   <tbody>

&nbsp;       <tr>

&nbsp;           <td>NAME\_ACHIEVE</td>

&nbsp;           <td>First Step</td>

&nbsp;           <td>Перший крок</td>

&nbsp;           <td>Pierwszy krok</td>

&nbsp;       </tr>

&nbsp;   </tbody>

</table>



<h2>📦 Instalacja (dla deweloperów)</h2>

<pre><code>git clone https://github.com/PanVena/SteamAchievementLocalizer.git

cd SteamAchievementLocalizer

pip install -r requirements.txt

python SteamAchievementLocalizer.py

</code></pre>

<p><strong>Wymagane:</strong> Python 3.10+, PyQt6, csv, re</p>



<h2>👥 Społeczność</h2>

<p>Dołącz do społeczności tłumaczy:<br>

<a href="https://t.me/linyvi\_sh\_ji" target="\_blank">👉 Kanał Telegram „Lazy AI`s”</a></p>



<h2>🛠 Szczegóły techniczne</h2>

<ul>

&nbsp;   <li>Działa z plikami <code>UserGameStatsSchema\_XXXX.bin</code> Steam</li>

&nbsp;   <li>Tekst wyciągany jest według wzoru <code>\\x01{language}\\x00{text}\\x00</code></li>

&nbsp;   <li><code>ukrainian</code> dodawany automatycznie, jeśli brak</li>

&nbsp;   <li>Edytowane są tylko wybrane języki, pozostałe bajty pozostają nienaruszone</li>

</ul>



<h2>🔖 Licencja</h2>

<p>MIT — używaj, modyfikuj, tłumacz, zapisuj i ciesz się.</p>



<h2>🧑‍💻 Autor</h2>

<p><strong>Vena</strong><br>

<a href="https://github.com/PanVena" target="\_blank">GitHub</a> | <a href="https://t.me/Pan\_Vena" target="\_blank">Telegram</a></p>

