**Дата:** 2026-04-09
**Статус:** draft

# SA-T065 — Phantom artifact paths when bash uses `cd subdir && tool src/file`

## Проблема

Когда в сессии выполняется bash-команда вида `cd /path/to/subdir && tool src/relative/file.jsx`, parser извлекает относительный путь `src/relative/file.jsx` из вывода команды (например, ESLint output) и резолвит его относительно **project root** (`$CWD`), а не директории `cd`.

Результат:
1. **Неверный путь:** `/project/src/relative/file.jsx` вместо `/project/subdir/src/relative/file.jsx`
2. **Неверное расширение:** `.jsx` может усекаться до `.js`

## Как воспроизвести

1. Сессия запускает ESLint из поддиректории:
   ```bash
   cd /Users/is/sproektirui/teplofort1-app/frontend && npx eslint src/components/heating/HeatLossCalculator.jsx
   ```
2. ESLint вывод содержит: `src/components/heating/HeatLossCalculator.jsx`
3. Parser видит relative path, берёт `$CWD = /Users/is/sproektirui` (project root), конструирует: `/Users/is/sproektirui/src/components/heating/HeatLossCalculator.js`
4. Такого пути не существует — phantom artifact

## Прецедент

Session `4208f1d2` (sproektirui, 2026-04-09). Команда:
```bash
cd /Users/is/sproektirui/teplofort1-app/frontend && npx eslint src/components/heating/HeatLossCalculator.jsx src/components/heating/DeviceCalculator.jsx src/constants/temperaturePresets.js --max-warnings=0
```
Породила 3 phantom artifacts:
- `/Users/is/sproektirui/src/components/heating/DeviceCalculator.js` (реальный: `teplofort1-app/frontend/src/...jsx`)
- `/Users/is/sproektirui/src/constants/temperaturePresets.js` (реальный: `teplofort1-app/frontend/src/...js`)
- `/Users/is/sproektirui/src/components/heating/HeatLossCalculator.js` (реальный: `teplofort1-app/frontend/src/...jsx`)

## Root cause

Parser не трекает `cd`-переход внутри bash command string. При резолве relative paths из tool results использует project root как base directory. Дополнительный баг: `.jsx` → `.js` (обрезается `x`).

## Рекомендуемый фикс

**A) Parse cd target from bash command:** При парсинге bash tool calls извлекать `cd /some/path` и использовать как base для последующих relative paths в этом tool result.

**B) Validate artifact existence:** Перед записью артефакта проверять `os.path.exists(resolved_path)`. Если не существует — скипнуть или логировать WARN.

**C) Fix extension normalization:** Убедиться что `.jsx` сохраняется как `.jsx`, а не усекается до `.js`.

Вариант B — минимальный патч, не требует парсинга bash. Вариант A — правильный root cause fix.

## Acceptance Criteria

- [ ] ESLint output с relative paths (`src/file.jsx`) не порождает phantom artifacts
- [ ] Phantom paths с неверным root не попадают в session_artifacts
- [ ] Расширение `.jsx` сохраняется корректно
