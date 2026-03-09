#!/bin/bash
# Bash скрипт для настройки cron задачи на Linux/macOS
# Запускает update_index.py каждый день в 6:00

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/update_index.py"
PYTHON_PATH=$(which python3)

if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python)
fi

if [ -z "$PYTHON_PATH" ]; then
    echo "Ошибка: Python не найден в PATH"
    exit 1
fi

echo "Настройка cron задачи для автоматического обновления индекса"
echo "Скрипт: $SCRIPT_PATH"
echo "Python: $PYTHON_PATH"
echo ""

# Создаем cron задачу (каждый день в 6:00)
CRON_JOB="0 6 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_PATH >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Проверяем, существует ли уже такая задача
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "Задача уже существует в crontab. Удаляю старую запись..."
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# Добавляем новую задачу
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron задача успешно добавлена!"
echo "Задача будет запускаться каждый день в 6:00"
echo ""
echo "Для просмотра задач используйте:"
echo "  crontab -l"
echo ""
echo "Для удаления задачи используйте:"
echo "  crontab -l | grep -v '$SCRIPT_PATH' | crontab -"

