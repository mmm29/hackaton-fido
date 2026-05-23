from fastmcp import FastMCP
import datetime
from pathlib import Path

mcp = FastMCP("AgenticStudioTools")


@mcp.tool()
def calculate(operation: str, a: float, b: float) -> str:
    """
    Виконує базові математичні операції.

    Args:
        operation: Тип операції: add, subtract, multiply, divide.
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

    return f"Помилка: невідома операція '{operation}'."


@mcp.tool()
def get_current_time() -> str:
    """Повертає поточну дату та системний час."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def analyze_and_plot_points(points: list[list[float]], degree: int = 2) -> dict:
    """
    Виконує статистичний аналіз набору точок, будує поліноміальну апроксимацію
    та зберігає графік matplotlib у PNG-файл.

    Args:
        points: Список точок у форматі [[x1, y1], [x2, y2], ...].
        degree: Степінь полінома для апроксимації.
    """
    if len(points) < 2:
        return {"error": "Потрібно передати щонайменше 2 точки."}

    if degree < 1:
        return {"error": "Степінь полінома має бути >= 1."}

    if degree >= len(points):
        return {"error": "Степінь полінома має бути меншою за кількість точок."}

    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.array([p[0] for p in points], dtype=float)
    y = np.array([p[1] for p in points], dtype=float)

    coefficients = np.polyfit(x, y, degree)
    polynomial = np.poly1d(coefficients)

    x_smooth = np.linspace(x.min(), x.max(), 200)
    y_smooth = polynomial(x_smooth)

    y_pred = polynomial(x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = output_dir / f"polynomial_plot_{timestamp}.png"

    plt.figure()
    plt.scatter(x, y, label="Input points")
    plt.plot(x_smooth, y_smooth, label=f"Polynomial degree {degree}")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Polynomial approximation")
    plt.legend()
    plt.grid(True)
    plt.savefig(plot_path)
    plt.close()

    return {
        "degree": degree,
        "coefficients": coefficients.tolist(),
        "r2": float(r2),
        "mean_y": float(np.mean(y)),
        "std_y": float(np.std(y)),
        "min_y": float(np.min(y)),
        "max_y": float(np.max(y)),
        "plot_path": str(plot_path),
    }


if __name__ == "__main__":
    mcp.run()