**Дата:** 2026-04-12
**Статус:** open
**Sev:** LOW

# SA-T082 — Meta-скиллы (archive-session, verify-archive) не должны тегироваться как skill

## Проблема

`archive-session` и `verify-archive` — meta-действия для архивации самой сессии. Они не описывают содержательную работу и не должны попадать в skill-теги. Это аналог SA-T071 (CLI builtins), но для пользовательских скиллов.

## Воспроизведение

Сессия `31408eb9` (autodev-v2, 2026-04-12):
- Содержательная работа: code review (`codereview-free` skill) — **корректный** skill-тег
- В конце: `/archive-session` → `skill: archive-session` — **ложный** skill-тег

### Воспроизведение 2 (2026-04-12, session `dee157dd`, autodev-v2)

- Содержательная работа: `/intro` + code review gate-tasks T055/T056 — **корректный** `skill: intro`
- В конце: `/archive-session` + `/verify-archive` → `skill: archive-session` попал в session_tags — **ложный**
- **Fix:** удалён из SQLite и export при verify-archive

### Воспроизведение 3 (2026-04-12, session `69d11152`, autodev-v2)

- Содержательная работа: `/codereview t046` — **корректный** skill-тег `codereview`
- В конце: `/archive-session` → `skill: archive-session` — **ложный** skill-тег, перезаписал `codereview`
- **Fix:** заменён на `codereview` в SQLite и export при verify-archive

### Воспроизведение 4 (2026-04-13, session `946bb737`, sales)

- Содержательная работа: `/next arb website` — **корректный** skill-тег `next`
- В конце: `/archive-session` → `skill: archive-session` — **ложный** skill-тег
- **Fix:** удалён из export при verify-archive

## Root cause

`detect_skills()` не различает содержательные скиллы (codereview, smoketest, fix, dev) от meta-скиллов (archive-session, verify-archive). Оба проходят одну и ту же детекцию через `<command-name>`.

## Рекомендация

Добавить `META_SKILLS` set в `detect_skills()`:

```python
META_SKILLS = {"archive-session", "verify-archive"}
```

Скиллы из этого набора пропускать при формировании skill-тегов. Они документируют workflow пользователя, а не предмет работы сессии.
