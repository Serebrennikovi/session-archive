**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T031 — Исправить жизненный цикл артефактов: created+deleted, multi-commit diff

## Customer-facing инкремент

После архивирования сессии `## Artifacts` не содержит файлов, которые были созданы и удалены в той же сессии. `## Diffs` для файлов с несколькими правками в сессии показывает суммарный diff от начала до конца, а не только последний коммит.

---

## Баги

### BUG-ARTIFACT-DELETED — файл создан и удалён в одной сессии появляется в Artifacts

**Симптом:** В сессии `autodev 88a8e972`: `feedback_commit_push.md` был создан через `Write` tool и затем удалён через `Bash rm`. В `session_artifacts` файл появился с action `created`, хотя на момент конца сессии файл не существует.

**Root cause:** Artifact tracker записывает `Write` → `created` при первом обнаружении и не отслеживает последующее удаление через `Bash rm/mv`. Нет crosscheck: "существует ли файл после всех операций?"

**Повторялось:** 1+ раз (2026-04-02, autodev 88a8e972).

**Fix:**
```python
class ArtifactLifecycleTracker:
    def __init__(self):
        self.events = {}  # path → list of (op, timestamp)

    def record_write(self, path, timestamp):
        self.events.setdefault(path, []).append(('write', timestamp))

    def record_delete(self, path, timestamp):
        self.events.setdefault(path, []).append(('delete', timestamp))

    def get_final_action(self, path):
        ops = self.events.get(path, [])
        if not ops:
            return None
        last_op = ops[-1][0]
        first_op = ops[0][0]

        if last_op == 'delete':
            if first_op == 'write' and len(ops) == 2:
                return 'created_and_deleted'  # полностью временный
            return 'deleted'
        elif first_op == 'write':
            return 'created'
        else:
            return 'modified'

def derive_artifacts(evidence):
    tracker = ArtifactLifecycleTracker()
    # Заполнить tracker из evidence.writes и evidence.bash_deletes
    ...
    artifacts = []
    for path in tracker.events:
        action = tracker.get_final_action(path)
        if action == 'created_and_deleted':
            continue  # не включать в artifacts — файл не пережил сессию
        artifacts.append({'path': path, 'action': action})
    return artifacts
```

Bash-команды для обнаружения удалений: `rm <path>`, `rm -f <path>`, `rm -rf <path>` — парсить первый позиционный аргумент после флагов.

---

### BUG-DIFF-SPLIT — файл правился в 2+ коммитах, diff показывает только последний

**Симптом:** В сессии `eb2f67de` файл задачи правился дважды — review-commit (добавлена code review секция) и accept-commit (финальный акцепт). В `## Diffs` появился только git_head diff последнего коммита; первый edit_snippet потерялся.

**Root cause:** `build_diffs()` для tracked-файлов делает `git diff base_commit..HEAD -- file` → получает суммарный diff, НО если `base_commit` совпадает с первым коммитом в сессии, то для файлов с несколькими коммитами в сессии теряется промежуточная история. Либо `diff_source=edit_snippet` перезаписывается `diff_source=git_head` при нахождении коммита.

**Повторялось:** 1+ раз (2026-04-02, sproektirui eb2f67de).

**Fix:**
```python
def build_file_diff(path, base_commit, head_commit, session_edits):
    """
    Стратегия приоритетов:
    1. Если есть base_commit → git diff base_commit..HEAD -- path (суммарный diff всей сессии)
       Это уже показывает ВСЕ изменения от начала до конца сессии, включая промежуточные.
    2. Если нет base_commit (untracked) → synthetic diff из earliest read + last write
    3. Никогда не терять edit_snippets — они fallback только если git diff недоступен
    """
    if base_commit:
        try:
            diff = subprocess.run(
                ['git', 'diff', f'{base_commit}..{head_commit}', '--', path],
                capture_output=True, text=True
            ).stdout
            if diff.strip():
                return {'source': 'git_range', 'content': diff, 'commits': [base_commit, head_commit]}
        except Exception:
            pass

    # Fallback: edit_snippets как было раньше
    ...
```

Ключевое изменение: `git diff base_commit..HEAD` УЖЕ агрегирует все промежуточные изменения. Если этот путь работает — edit_snippets не нужны. Проверить, что `base_commit` корректно определяется в начале каждой сессии.

Если файл был в нескольких коммитах И `base_commit` не определён (rare case) — конкатенировать все `edit_snippet` для этого файла в единый блок с маркерами коммитов.

---

## Scope

- `ArtifactLifecycleTracker` — отслеживать Write + Bash rm/mv в рамках сессии
- Файлы с итоговым action `created_and_deleted` — исключать из `session_artifacts`
- `build_file_diff()` — использовать `git diff base_commit..HEAD` как primary source
- Обеспечить корректное определение `base_commit` в начале парсинга сессии

## Out of scope

- Отслеживание переименований файлов внутри сессии (покрыто SA-T022)
- Обработка файлов вне git (untracked) — покрыто SA-T021

---

## Как протестировать

1. Создать JSONL с Write на `tmp.md` + Bash `rm tmp.md` → `session_artifacts` не содержит `tmp.md`
2. Создать JSONL с двумя Edit на один файл + двумя git commits → `session_diffs` показывает суммарный diff обоих commits
3. Создать JSONL с Write + Edit на один файл (без git commit) → diff строится от Write-baseline до финального Edit

## Критерии приёмки

1. `feedback_commit_push.md`-подобные временные файлы не попадают в `session_artifacts`
2. Для файла с 2 коммитами в сессии diff охватывает оба изменения (не только последний)
3. `git diff base_commit..HEAD` используется как primary diff source для tracked файлов
