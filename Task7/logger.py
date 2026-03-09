"""
Модуль для логирования запросов к RAG-боту.
Сохраняет каждый запрос с метаданными в JSONL формат.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class RAGLogger:
    """
    Логгер для записи запросов к RAG-боту.
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Инициализация логгера.
        
        Args:
            log_file: Путь к файлу лога. Если None, используется logs.jsonl в текущей директории.
        """
        if log_file is None:
            script_dir = Path(__file__).parent.absolute()
            log_file = script_dir / "logs.jsonl"
        
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_query(
        self,
        query: str,
        answer: str,
        chunks: List[Dict],
        reasoning: str,
        success: Optional[bool] = None,
        answer_length: Optional[int] = None
    ) -> Dict:
        """
        Логирует запрос к RAG-боту.
        
        Args:
            query: Текст запроса пользователя
            answer: Ответ бота
            chunks: Список найденных чанков
            reasoning: Объяснение процесса поиска
            success: Флаг успешности ответа (если None, вычисляется автоматически)
            answer_length: Длина ответа (если None, вычисляется автоматически)
            
        Returns:
            Словарь с записанными данными
        """
        # Вычисляем длину ответа
        if answer_length is None:
            answer_length = len(answer)
        
        # Извлекаем источники из чанков
        sources = []
        for chunk in chunks:
            source_info = {
                "title": chunk.get("metadata", {}).get("title", "Unknown"),
                "filename": chunk.get("metadata", {}).get("filename", "Unknown"),
                "distance": chunk.get("distance")
            }
            sources.append(source_info)
        
        # Определяем успешность ответа
        if success is None:
            success = self._evaluate_success(query, answer, chunks)
        
        # Формируем запись лога
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "answer_length": answer_length,
            "chunks_found": len(chunks) > 0,
            "chunks_count": len(chunks),
            "sources": sources,
            "success": success,
            "reasoning": reasoning
        }
        
        # Записываем в файл (JSONL формат)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return log_entry
    
    def _evaluate_success(
        self,
        query: str,
        answer: str,
        chunks: List[Dict]
    ) -> bool:
        """
        Оценивает успешность ответа на основе различных критериев.
        
        Args:
            query: Запрос пользователя
            answer: Ответ бота
            chunks: Найденные чанки
            
        Returns:
            True, если ответ считается успешным
        """
        # Критерии неуспешного ответа
        failure_indicators = [
            "я не знаю",
            "не найдено",
            "нет информации",
            "не могу ответить",
            "i don't know",
            "not found",
            "no information",
            "cannot answer"
        ]
        
        answer_lower = answer.lower()
        
        # Если в ответе есть индикаторы неуспеха
        if any(indicator in answer_lower for indicator in failure_indicators):
            return False
        
        # Если не найдено чанков
        if len(chunks) == 0:
            return False
        
        # Если ответ слишком короткий (менее 20 символов)
        if len(answer) < 20:
            return False
        
        # Если ответ содержит только техническую информацию об ошибке
        if "ошибка" in answer_lower or "error" in answer_lower:
            return False
        
        return True
    
    def get_all_logs(self) -> List[Dict]:
        """
        Читает все записи из лога.
        
        Returns:
            Список всех записей лога
        """
        logs = []
        if not self.log_file.exists():
            return logs
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        
        return logs
    
    def clear_logs(self):
        """
        Очищает файл лога.
        """
        if self.log_file.exists():
            self.log_file.unlink()
        print(f"Лог очищен: {self.log_file}")

