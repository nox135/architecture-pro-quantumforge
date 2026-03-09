"""
Скрипт для проверки установки всех необходимых зависимостей.
"""

import sys

def check_module(module_name, import_name=None):
    """Проверяет наличие модуля."""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✓ {module_name} установлен")
        return True
    except ImportError as e:
        print(f"✗ {module_name} НЕ установлен: {e}")
        return False

def main():
    """Проверяет все необходимые модули."""
    print("Проверка установки зависимостей...")
    print("=" * 50)
    
    modules = [
        ("sentence-transformers", "sentence_transformers"),
        ("chromadb", "chromadb"),
        ("langchain", "langchain"),
        ("langchain-core", "langchain_core"),
        ("langchain-community", "langchain_community"),
        ("langchain-text-splitters", "langchain_text_splitters"),
        ("tqdm", "tqdm"),
    ]
    
    results = []
    for module_name, import_name in modules:
        results.append(check_module(module_name, import_name))
    
    print("=" * 50)
    
    if all(results):
        print("\n✓ Все зависимости установлены корректно!")
        print("Можно запускать build_index.py")
        return 0
    else:
        print("\n✗ Некоторые зависимости не установлены.")
        print("\nДля установки выполните:")
        print("  pip install -r requirements.txt")
        print("\nИли установите по отдельности:")
        for module_name, _ in modules:
            if not results[modules.index((module_name, _))]:
                print(f"  pip install {module_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

