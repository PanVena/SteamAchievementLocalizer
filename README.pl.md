[![uk](https://img.shields.io/badge/українська-blue.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.uk.md)
[![en](https://img.shields.io/badge/english-red.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.md)
<h1>🏆 Lokalizator osiągnięć Steam od Veny</h1>

<p><strong>Steam Achievement Localizer</strong> to narzędzie GUI oparte na PyQt6 do edycji plików osiągnięć Steam (UserGameStatsSchema_xxx.bin).
Pozwala tłumaczyć i lokalizować opisy osiągnięć oraz zapisywać zmiany bezpośrednio w folderze Steam lub jako osobny plik.</p>

<p><a class="button-link" href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest" target="_blank">👉 Pobierz najnowszą wersję 👈</a></p>

![Screenshot](assets/scrn_pl.png)

## 📌 Funkcje
- Automatyczne wykrywanie folderu Steam (przez Rejestr Windows).
- Ładowanie pliku `UserGameStatsSchema_*.bin`:
  - ręcznie,
  - lub automatycznie według ID gry.
- Podgląd i edycja tabeli osiągnięć.
- Wyszukiwanie według kolumny.
- Eksport do CSV:
  - wszystkie języki naraz,
  - specjalny format do tłumaczenia.
- Import tłumaczeń z CSV z powrotem do aplikacji.
- Automatyczne wsparcie dla języka ukraińskiego (dodaje kolumnę, jeśli jej brakuje).
- Podmiana tłumaczeń bezpośrednio w plikach `.bin`.
- Zapis:
  - bezpośrednio do folderu Steam,
  - lub w dowolne miejsce.
- Wielojęzyczny interfejs (angielski, ukraiński).

<blockquote>
   <h4> <p><strong><i>W przewodnikach dla tłumaczy zalecamy umieszczenie pliku w „C:\Program Files (x86)\Steam\appcache\stats\”, zastępując oryginał.</i></strong></p></h4>
</blockquote>

<p><strong>🧯 Jeśli napotkasz błędy — usuń plik tutaj, zrestartuj Steam i wejdź na stronę gry w swojej bibliotece:</strong><br>
<code>C:\Program Files (x86)\Steam\appcache\stats\UserGameStatsSchema_XXXX.bin</code><br>
<strong>Lub znajdź go w jego naturalnym środowisku :)</strong></p>


<h2>👥 Społeczność</h2>
<p>Dołącz do społeczności tłumaczy:<br>
<a href="https://t.me/linyvi_sh_ji" target="_blank">👉 Kanał Telegram „Leniwi SI”</a></p>

<h2>🛠 Szczegóły techniczne</h2>
<ul>
    <li>Działa z plikami <code>UserGameStatsSchema_XXXX.bin</code> Steam</li>
    <li>Tekst wyciągany jest według wzoru <code>\x01{language}\x00{text}\x00</code></li>
    <li><code>ukrainian</code> dodawany automatycznie, jeśli brak</li>
    <li>Edytowane są tylko wybrane języki, pozostałe bajty pozostają nienaruszone</li>
</ul>

<h2>🔖 Licencja</h2>
<p>MIT — używaj, modyfikuj, tłumacz, zapisuj i ciesz się.</p>

<h2>🧑‍💻 Autor</h2>
<p><strong>Vena</strong><br>
<a href="https://github.com/PanVena" target="_blank">GitHub</a> | <a href="https://t.me/Pan_Vena" target="_blank">Telegram</a></p>
