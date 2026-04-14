**Дата:** 2026-04-12
**Статус:** open
**Sev:** LOW

# SA-T080 — Open Issues: захват строк из содержимого созданных файлов

## Проблема

Секция `## Open Issues` содержит вырванные из контекста строки из файлов, которые ассистент создал через Write tool, а не реальные открытые проблемы сессии.

## Воспроизведение

Сессия `a8e931c1` (autodev-v2, 2026-04-12): Open Issues = `Edge cases:** stagnation, human-blocker explain (exit code 2), malformed findings, context loading (optional/required files), findings round-trip, freeze threshold`

Это строка из файла `ADV-T055_s06_spec_hardening_integration_tests.md`, секция Scope. Парсер вырвал её из Write tool result content. Сломан markdown (начинается с `Edge cases:**` без первой звёздочки).

## Root cause

Связан с SA-T053 — парсер не отличает содержимое записываемых файлов от реальных issue indicators. Фильтрация должна исключать контент внутри Write/Edit tool results.

### Воспроизведение 2 (2026-04-13, session `ba9d7314`, autodev-v2)

Open Issues = `Now let me verify the remaining critical areas.` — это переходная фраза из assistant-сообщения между двумя tool calls (Read). Не является open issue, а просто narrative transition.

**Новый подтип:** парсер захватывает не только content из Write/Edit results, но и обычные переходные фразы из assistant text.

## Рекомендация

При сканировании Open Issues пропускать контент внутри tool_result блоков с tool_use_id, соответствующих Write/Edit tools. Также фильтровать generic transition phrases ("Let me...", "Now let me...", "I'll now...").

### Воспроизведение 3 (2026-04-13, session `5cf74de4`, autodev-v2)

Open Issues = `["Строка 29: - | 2 | MEDIUM | MEDIUM | Реалистичный blocker, корректен | — ...", "Open Issues:**"]`

Парсер захватил строку из **markdown-таблицы калибровки findings** в assistant message. Таблица содержала `| 2 | MEDIUM | MEDIUM | ...` — парсер принял это за open issue indicator. Второй элемент `"Open Issues:**"` — markdown header из assistant text.

**Новый подтип:** парсер захватывает строки из markdown-таблиц в assistant responses, если они содержат "MEDIUM"/"HIGH" паттерны.
