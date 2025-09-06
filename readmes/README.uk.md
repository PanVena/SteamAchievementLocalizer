[![en](https://img.shields.io/badge/english-red.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.md)
[![pl](https://img.shields.io/badge/polski-green.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/readmes/README.pl.md)

<h1>🏆 Локалізатор досягнень Стіму від Вени</h1>

<p><strong>Steam Achievement Localizer</strong> — є інструментом із графічним інтерфейсом на базі **PyQt6** для редагування файлів досягнень Steam (`UserGameStatsSchema_xxx.bin`).  
Він дозволяє перекладати та локалізувати описи досягнень, а також зберігати зміни безпосередньо у теку Steam або у окремий файл.  

<p><a class="button-link" href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest" target="_blank">👉 Завантажити останню версію 👈</a></p>


![Скрін](assets/screens/scrn_ukr.png)



## 📌 Можливості
- Автоматичне визначення теки Steam (через реєстр Windows).  
- Завантаження файлу `UserGameStatsSchema_*.bin`:
  - вручну,  
  - або автоматично за ID гри.  
- Перегляд і редагування таблиць досягнень.  
- Пошук по стовпцях.  
- Експорт у CSV:
  - всі мови одразу,  
  - спеціальний формат для перекладу.  
- Імпорт перекладів із CSV назад у програму.  
- Автоматичне додавання української (якщо відсутня у файлі).  
- Заміна перекладів безпосередньо у `.bin` файлах.  
- Збереження:
  - напряму у теку Steam,  
  - або у довільне місце.  
- Багатомовний інтерфейс (англійська, українська, польська).  

<blockquote>
   <h4> <p><strong><i>У посібничках до українізаторів кажемо, що файлик кидать до "C:\Program Files (x86)\Steam\appcache\stats\", з заміною.</i></strong></p></h4>
</blockquote>

<p><strong>🧯 У разі помилок — видали файл отут і перезапусти стім і зайшовши на сторінку гри у бібліотеці:</strong><br>
<code>C:\Program Files (x86)\Steam\appcache\stats\UserGameStatsSchema_XXXX.bin</code><br>
<strong>Або знайшовши його у природному середовищі)</strong></p>


<h2>👥 Спільнота</h2>
<p>Приєднуйтесь до спілки перекладачів:<br>
<a href="https://t.me/linyvi_sh_ji" target="_blank">👉 Телеграм-канал "Ліниві ШІ"</a></p>

<h2>💰 Подякувати</h2>
<p>Якщо софт зекономив тобі час і нерви — можеш «перекинути кілька біткоїнів гривнею» 😄<br>
<a href="https://send.monobank.ua/jar/9V3wRMZD7C" target="_blank">➡ ТУТ 🌻 Mono Jar</a></p>

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
