# Описание словаря замен терминов

## Источник данных

**Исходная вселенная:** Star Wars (Звёздные войны)

**Источник страниц:** starwars.fandom.com

## Принцип создания словаря

Словарь замен создан для трансформации известной вселенной Star Wars в уникальную вымышленную вселенную, которую LLM не может распознать из своих обучающих данных. При этом сохранена логическая структура и стиль оригинального мира.

## Категории замен

### Персонажи
- **Герои:** Luke Skywalker → Kael Thorne, Princess Leia → Aria Zephyr, Han Solo → Jax Riven
- **Злодеи:** Darth Vader → Xarn Velgor, Emperor Palpatine → Lord Malachar
- **Наставники:** Obi-Wan Kenobi → Miran Kestrel, Yoda → Zephyr
- **Дроиды:** R2-D2 → Cipher-7, C-3PO → Protocol-9

### Технологии и оружие
- **Сила:** The Force → Synth Flux
- **Оружие:** Lightsaber → Flux Blade, Blaster → Plasma Rifle
- **Корабли:** Millennium Falcon → Stardrift, X-wing → Nexus Fighter, TIE Fighter → Void Dart

### Организации и фракции
- **Ордены:** Jedi → Flux Wardens, Sith → Void Seekers
- **Политические силы:** Rebel Alliance → Free Coalition, Galactic Empire → Void Dominion
- **Военные:** Stormtrooper → Void Guard, Clone Trooper → Replica Guard

### Планеты и локации
- Tatooine → Zephyr Prime
- Coruscant → Nexus Central
- Alderaan → Serenity
- Hoth → Frostfall
- Dagobah → Mistwood
- Endor → Verdant

### События
- The Clone Wars → The Replica Wars
- Battle of Yavin → Battle of Nexus
- Battle of Hoth → Battle of Frostfall

### Расы
- Wookiee → Gronk
- Ewok → Furling

### Концепции
- Dark Side → Void Path
- Light Side → Flux Path
- Hyperspace → Void Jump

## Особенности замены

1. **Сохранение стиля:** Вымышленные названия сохраняют фантастический стиль оригинала
2. **Логическая связность:** Связанные термины заменяются согласованно (например, все термины, связанные с "Force", содержат "Flux")
3. **Уникальность:** Все замены созданы так, чтобы не совпадать с известными вселенными
4. **Читаемость:** Тексты остаются понятными и логичными после замены

## Использование

Словарь используется скриптом `03_replace_terms.py` для автоматической замены всех упоминаний оригинальных терминов на вымышленные названия во всех документах базы знаний.

Файл `terms_map.json` содержит полный словарь в формате JSON для программного использования.

