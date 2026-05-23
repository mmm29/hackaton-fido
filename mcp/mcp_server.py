from fastmcp import FastMCP
import datetime

# Ініціалізація MCP-сервера.
mcp = FastMCP("AgenticStudioTools")


# 1. Інструмент: Калькулятор
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


# 2. Інструмент: Системний час та дата
@mcp.tool()
def get_current_time() -> str:
    """Повертає поточну дату та системний час."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
