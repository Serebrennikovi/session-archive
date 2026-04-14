**Дата:** 2026-04-08
**Статус:** open
**Severity:** MEDIUM

# SA-T054 — Write (overwrite) файлов не попадает в Diffs

## Проблема

Когда файл перезаписывается целиком через Write tool (не Edit), его diff не попадает в экспортный .md. Файл корректно отображается в Artifacts как `(modified)`, но секция Diffs не содержит соответствующего diff-блока.

### Воспроизведение (2026-04-08, session 23eb9256)

1. `ARB-HANDOFF.md` был перезаписан через Write tool (полный overwrite существующего файла)
2. В Artifacts: `/Users/is/sales/05_ARB_arbitra_website/ARB-HANDOFF.md (modified)` — корректно
3. В Diffs: diff-блок для ARB-HANDOFF.md отсутствует
4. Другие файлы (index.html через Edit, DESIGN.md и ui-kit.html через Write на новые файлы) — дифы присутствуют

### Вероятная причина

Парсер генерирует synthetic diff для Write на **новые** файлы (DESIGN.md, ui-kit.html → `@@ -0,0 +1,...`), но для Write на **существующие** файлы (overwrite) не генерирует diff, потому что не имеет "before" state файла.

Edit-вызовы содержат `old_string`/`new_string` — из них diff строится тривиально. Write-вызовы содержат только новый content — для diff нужно знать предыдущее содержимое, которого в JSONL нет.

## Рекомендация по фиксу

1. **Минимальный фикс**: для Write на существующий файл генерировать placeholder diff:
   ```diff
   --- a/path/to/file
   +++ b/path/to/file
   @@ -1,? +1,N @@
   [full file overwrite — N lines]
   ```
2. **Лучший фикс**: если в сессии ранее был Read того же файла — использовать его content как "before" state для полноценного diff
3. **Идеальный фикс**: при обнаружении Write на существующий файл, проверить git diff если файл под git-контролем
