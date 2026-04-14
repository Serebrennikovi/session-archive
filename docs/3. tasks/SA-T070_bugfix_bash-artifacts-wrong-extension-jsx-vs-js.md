**Дата:** 2026-04-09
**Статус:** draft
**Severity:** MEDIUM

# SA-T070 — Bash-артефакты из grep получают неверное расширение .js вместо .jsx

## Проблема

Когда сессия использует Bash-команды для grep/поиска по `.jsx` файлам (не через Read tool), парсер добавляет эти файлы в artifacts как `.js` (без `x`), неверно определяя расширение.

## Воспроизведение — сессия 837e25fc (sproektirui, 2026-04-09)

Сессия выполняла Bash grep команды:
```bash
grep -n "handleOpenModal\|onClick" .../CategorySection.jsx | head -30
grep -n "onClick\|role\|button" .../SeriesCard.jsx | head -30
grep -n "Route\|path\|catalog" .../App.jsx | head -20
grep -n "onClick\|role\|button" .../BrandCard.jsx | head -20
```

В `session_artifacts` попали:
- `CategorySection.js` (read) — должно быть `CategorySection.jsx`
- `SeriesCard.js` (read) — должно быть `SeriesCard.jsx`
- `App.js` (read) — должно быть `App.jsx`
- `main.js` (read) — никогда не читался (ни Read, ни grep)
- `CatalogPage.js` ×2 (read) — должно быть `CatalogPage.jsx`
- `BrandCard.js` (read) — должно быть `BrandCard.jsx`

Дополнительная проблема: `main.js` появился в artifacts несмотря на то, что ни один Bash/Read вызов не затрагивал этот файл в сессии.

## Root cause (гипотеза)

Парсер Bash tool_result использует regex типа `(\S+\.)js\b` или `\w+\.js` для извлечения файловых путей из shell-вывода. Если regex не покрывает `.jsx`, путь `CategorySection.jsx` матчится как `CategorySection.j` + остаток, или regex захватывает `.js` как терминатор слова.

Альтернативно: парсер нормализует расширения (`.jsx` → `.js`) считая их эквивалентными.

`main.js` — возможно phantomed из git diff HEAD или из контекстного сканирования, не связан с Bash grep.

## Как отличить от SA-T056

SA-T056: grep artifacts вообще не должны создаваться.
SA-T070: если создаются — расширение неверное (`.js` вместо `.jsx`).

Оба дефекта сосуществуют в одной сессии.

## Рекомендация по фиксу

1. **Regex update:** поменять `\.js\b` на `\.jsx?\b` в artifact path extraction из Bash output
2. **Validation:** после извлечения пути из Bash output — проверять существование файла. Если `CategorySection.js` не существует, но `CategorySection.jsx` существует — использовать реальный файл
3. **main.js / фантомные артефакты без tool call evidence:** применить фильтр SA-T056 (только файлы с явным Read/Edit/Write tool call)

## Acceptance Criteria

- [ ] `CategorySection.jsx` (не `.js`) в artifacts при grep-команде на `.jsx` файл
- [ ] `main.jsx` не появляется, если не было Read/grep tool call с этим файлом
- [ ] Проверка: `find .jsx` в Bash output → правильное расширение в artifacts

## Прецедент #2 — session fb6419f7 (sproektirui, 2026-04-09)

Сессия Bash grep: `grep -n "calcId\|connection_type" .../ResultTabs.jsx`
В artifacts попал: `ResultTabs.js` (read) — должно быть `ResultTabs.jsx`.
Дополнительно: `routers/calc.py` из Bash grep добавлен как artifact (SA-T056).

## Связанные баги

- SA-T056: grep artifacts вообще не должны попадать (предшествующий класс)
- SA-T065: phantom paths из cd-subdir bash
- SA-T028: artifact noise reduction (bash mv/rm)
