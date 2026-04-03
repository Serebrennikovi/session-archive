---
description: "Вынести часто повторяющиеся баги из BUGS.md в задачу и очистить документ"
---

# Bugs-to-Task — создать задачу из повторяющихся багов

Аргументы: `$ARGUMENTS` — опционально, номер группы или название бага для фокуса.

---

## Шаг 1: Найди BUGS.md

Определи рабочий проект: git rev-parse --show-toplevel (или CWD). Найди `BUGS.md` в корне.

Если не найдено → сообщи "BUGS.md не найден" и стоп.

---

## Шаг 2: Найди часто повторяющиеся непокрытые баги

Прочитай BUGS.md. Обрати внимание на:
- Таблицу трекинга в начале (`## Трекинг повторяющихся багов → задачи`) — какие баги уже имеют задачи
- Строки таблиц сессий вида `| BUG-XXX | ...` — считай количество уникальных сессий, где встречается каждый BUG-ID

**Считаем только покрытые задачами** как "уже обработаны" (статус draft/done в tracking table).

Построй топ-5 непокрытых багов по частоте. Сгруппируй связанные (например BUG-DIFF-EMPTY-LINES + BUG-DIFF-DOUBLE-SLASH = одна группа).

Выведи в чат:

```
## Топ повторяющихся непокрытых багов

| # | Баг(и) | Сессий | Root cause (предположение) |
|---|--------|--------|---------------------------|
| 1 | BUG-XXX | N | ... |
| 2 | BUG-YYY, BUG-ZZZ | N | ... |
...

Предлагаю создать задачи для групп #1 и #2. Продолжить?
```

**ОСТАНОВИСЬ И ЖДИ ПОДТВЕРЖДЕНИЯ.** Если пользователь сказал "делай" / "да" / "go" — продолжай. Если указал конкретные группы — используй только их.

---

## Шаг 3: Определи следующий номер задачи

Найди все файлы `SA-T*.md` в `docs/3. tasks/` (включая Done/). Возьми максимальный номер, следующая задача = max + 1.

```bash
find "docs/3. tasks" -name "SA-T*.md" | grep -oE 'T[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1
```

---

## Шаг 4: Создай файл задачи

Для каждой группы багов создай `docs/3. tasks/SA-TНNN_bugfix_<slug>.md`.

Структура файла (обязательно все секции):

```markdown
**Дата:** YYYY-MM-DD
**Статус:** draft
**Спецификация:** —

# SA-TНNN — Исправить <краткое название>

## Customer-facing инкремент

После архивирования сессии <что улучшится для пользователя>.

---

## Баги

### BUG-XXX — <название>

**Симптом:** <что видно>

**Root cause:** <почему происходит>

**Повторялось:** <N>+ раз, каждый раз исправляется вручную.

**Fix:**
<конкретный код или алгоритм фикса>

---

[Повтори для каждого бага группы]

## Scope

- <что делаем>

## Out of scope

- <что не делаем>

---

## Как протестировать

1. <шаги>

## Критерии приёмки

1. <проверяемый результат>
```

Для root cause и fix — используй информацию из секций **"Наблюдения"** / **"Новые баги"** соответствующих сессий в BUGS.md, там обычно есть описание причины и рекомендации по фиксу.

---

## Шаг 5: Обнови таблицу трекинга в BUGS.md

В секции `## Трекинг повторяющихся багов → задачи` добавь строки для новых задач:

```
| BUG-XXX, BUG-YYY | [SA-TНNN](docs/3. tasks/SA-TНNN_bugfix_slug.md) | draft |
```

---

## Шаг 6: Удали покрытые строки из таблиц сессий

Используй Python-скрипт (запусти через Bash) для обработки BUGS.md:

```python
import re

with open('BUGS.md', 'r') as f:
    content = f.read()

# Паттерны покрытых багов — все баги что теперь в задачах (включая новые SA-TНNN)
covered_patterns = [/* сюда все паттерны из всех задач в tracking table */]
covered_re = re.compile('|'.join(covered_patterns))

header_match = re.search(r'^## Сессия ', content, re.MULTILINE)
header = content[:header_match.start()]
sessions_text = content[header_match.start():]
session_blocks = re.split(r'(?=^## Сессия )', sessions_text, flags=re.MULTILINE)

kept_blocks = []
removed_count = 0

for block in session_blocks:
    if not block.strip():
        continue
    lines = block.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('| BUG') and covered_re.search(line):
            continue  # удаляем покрытую строку
        new_lines.append(line)

    # Проверяем остались ли непокрытые баги
    remaining = [l for l in new_lines if l.startswith('| BUG-')]
    remaining = [l for l in remaining if not l.startswith('| BUG |')]

    if not remaining:
        removed_count += 1  # сессия пуста — не включаем
    else:
        kept_blocks.append('\n'.join(new_lines))

result = header + ''.join(kept_blocks)
with open('BUGS.md', 'w') as f:
    f.write(result)

print(f"Удалено пустых сессий: {removed_count}")
print(f"Осталось сессий: {len(kept_blocks)}")
```

Сформируй `covered_patterns` из ВСЕХ багов, у которых есть задача в tracking table (включая только что добавленные).

---

## Шаг 7: Обнови SA-HANDOFF.md

В секцию `## Активные задачи` добавь строки для новых задач:

```
| [SA-TНNN](3. tasks/SA-TНNN_bugfix_slug.md) | <описание> | draft |
```

В `### Приоритет 1: Стабильность` замени/добавь ссылки на новые задачи.

---

## Шаг 8: Отчёт

Выведи итог:

```
## Результат bugs-to-task

Создано задач: N
- SA-TНNN — <название> (покрывает: BUG-XXX, BUG-YYY, N сессий)
- ...

BUGS.md:
- Удалено строк с покрытыми багами: ~N
- Удалено пустых сессий: N (осталось: N)

SA-HANDOFF.md обновлён.
```
