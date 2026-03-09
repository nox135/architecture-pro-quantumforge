"""
Утилита для завершения процесса, занимающего указанный порт.
Использование: python kill_port.py [PORT]
"""

import sys
import subprocess
import re


def kill_process_on_port(port: int):
    """Завершает процесс, использующий указанный порт."""
    try:
        # Находим процесс, использующий порт
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="cp866"  # Для Windows русской локали
        )
        
        # Ищем PID процесса, слушающего порт
        pid = None
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                # Извлекаем PID из строки
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    break
        
        if not pid:
            print(f"✗ Процесс на порту {port} не найден")
            return False
        
        # Завершаем процесс
        print(f"Найден процесс с PID {pid} на порту {port}")
        result = subprocess.run(
            ["taskkill", "/PID", pid, "/F"],
            capture_output=True,
            text=True,
            encoding="cp866"
        )
        
        if result.returncode == 0:
            print(f"✓ Процесс {pid} успешно завершен")
            return True
        else:
            print(f"✗ Ошибка при завершении процесса: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"✗ Неверный номер порта: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"Завершение процесса на порту {port}...")
    success = kill_process_on_port(port)
    sys.exit(0 if success else 1)

