# Восстановление больших файлов

Этот репозиторий содержит большие файлы, которые были разбиты на части для загрузки на GitHub.

## Файлы в архиве:
- `LaunchTGV4.2.1/LaunchTG.exe` (118.64 MB)
- `LaunchTG_extracted/rsrc_section.bin` (119.58 MB)

## Как восстановить файлы:

### На Linux/Mac:
```bash
cat large_files_backup.tar.gz.part_* > large_files_backup.tar.gz
tar -xzf large_files_backup.tar.gz
```

### На Windows (PowerShell):
```powershell
Get-Content large_files_backup.tar.gz.part_* -Raw | Set-Content large_files_backup.tar.gz -Encoding Byte
tar -xzf large_files_backup.tar.gz
```

### На Windows (Git Bash):
```bash
cat large_files_backup.tar.gz.part_* > large_files_backup.tar.gz
tar -xzf large_files_backup.tar.gz
```

После выполнения команд файлы будут восстановлены в исходные папки.
