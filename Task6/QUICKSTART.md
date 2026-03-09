# Быстрый старт

## 1. Установка зависимостей

```bash
cd Task6
pip install -r requirements.txt
```

## 2. Первый запуск (ручной)

```bash
python update_index.py
```

## 3. Настройка автоматического запуска

### Windows

Откройте PowerShell от имени администратора:

```powershell
cd Task6
.\schedule_windows.ps1
```

### Linux/macOS

```bash
cd Task6
chmod +x schedule_linux.sh
./schedule_linux.sh
```

## 4. Проверка работы

После первого запуска проверьте:
- Логи в `logs/update_index_YYYYMMDD.log`
- Результат в `logs/update_result_*.json`
- Состояние в `update_state.json`

## 5. Тестирование

Добавьте новый файл в `Task2/knowledge_base/` и запустите скрипт снова:

```bash
echo "Test content" > ../Task2/knowledge_base/Test.txt
python update_index.py
```

Подробная документация в [README.md](README.md).

