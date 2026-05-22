from fastmcp import FastMCP

# Ініціалізуємо сервер інструментів.
# Цю назву побачить LLM Макса при підключенні.
mcp = FastMCP("AgenticStudioTools")

@mcp.tool()
def calculate(operation: str, a: float, b: float) -> str:
    """
    Виконує базові математичні операції.

    Args:
        operation: Тип операції. Варіанти: 'add', 'subtract', 'multiply', 'divide'.
        a: Перше число.
        b: Друге число.
    """
    if operation == "add":
        return str(a + b)
    elif operation == "subtract":
        return str(a - b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        if b == 0:
            return "Помилка: ділення на нуль неможливе."
        return str(a / b)
    else:
        return f"Помилка: невідома операція '{operation}'."

if __name__ == "__main__":
    print("Запуск MCP Сервера 'AgenticStudioTools'...")
    mcp.run()