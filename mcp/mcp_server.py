from fastmcp import FastMCP
import requests
import json
import datetime

# Ініціалізація сервера
mcp = FastMCP("InsuranceFraudInvestigator")


# ==========================================
# 1. РЕАЛЬНА ПЕРЕХРЕСНА ПЕРЕВІРКА ПОГОДИ
# ==========================================
@mcp.tool()
def check_historical_weather(latitude: float, longitude: float, date_str: str) -> str:
    """
    Перевіряє реальну погоду за вказаними координатами та датою (Open-Meteo API).
    Формат дати: 'YYYY-MM-DD'. Використовуй для перевірки слів клієнта про ожеледицю чи зливу.
    """
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={date_str}&end_date={date_str}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            max_t = daily.get("temperature_2m_max", ["N/A"])[0]
            min_t = daily.get("temperature_2m_min", ["N/A"])[0]
            precip = daily.get("precipitation_sum", ["0"])[0]

            report = f"Фактична погода {date_str}:\nТемпература: від {min_t}°C до {max_t}°C.\nОпади: {precip} мм.\n"
            if float(precip) > 5:
                report += "Висновок: Були значні опади (дощ/сніг)."
            elif float(min_t) < 0 and float(precip) > 0:
                report += "Висновок: Висока ймовірність ожеледиці."
            else:
                report += "Висновок: Опадів майже не було, сухо."
            return report

        return "Не вдалося отримати дані про погоду з архіву."
    except Exception as e:
        return f"Помилка API погоди: {str(e)}"


# ==========================================
# 2. РЕАЛЬНИЙ ДЕКОДЕР VIN-КОДУ
# ==========================================
@mcp.tool()
def decode_vin_nhtsa(vin_code: str) -> str:
    """
    Розшифровує VIN-код через реальну базу даних NHTSA.
    Повертає заводські характеристики: марку, модель, рік та тип кузова.
    """
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_code}?format=json"
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("Results", [])[0]
            make = results.get("Make", "Unknown")
            model = results.get("Model", "Unknown")
            year = results.get("ModelYear", "Unknown")
            body = results.get("BodyClass", "Unknown")

            if make and make != "Unknown":
                return f"Офіційні дані NHTSA для VIN {vin_code}:\nАвто: {year} {make} {model}\nКузов: {body}"
            else:
                return f"Помилка: VIN {vin_code} не знайдено в базі."
        return "Сервіс перевірки VIN тимчасово недоступний."
    except Exception as e:
        return f"Помилка запиту до бази VIN: {str(e)}"


# ==========================================
# 3. ДЕТЕКТИВ З ФІЗИКИ ДТП (Логічний аналізатор)
# ==========================================
@mcp.tool()
def analyze_damage_consistency(impact_direction: str, damaged_parts_json: str) -> str:
    """
    Аналізує, чи відповідають заявлені пошкоджені деталі напрямку удару в ДТП.
    impact_direction: 'front', 'rear', 'side_left', 'side_right'
    damaged_parts_json: JSON-список деталей, наприклад '["radiator", "rear_bumper", "headlight"]'
    """
    try:
        parts = json.loads(damaged_parts_json)

        # База знань фізичного розташування деталей
        front_parts = ["radiator", "headlight", "front_bumper", "hood", "grille"]
        rear_parts = ["rear_bumper", "trunk", "tailgate", "taillight", "exhaust"]

        anomalies = []

        for part in parts:
            part_lower = part.lower().strip()

            # Якщо удар ззаду, але міняють передні деталі
            if impact_direction == "rear" and any(
                fp in part_lower for fp in front_parts
            ):
                anomalies.append(
                    f"Деталь '{part}' знаходиться спереду, але заявлений удар був ззаду ('{impact_direction}')."
                )

            # Якщо удар спереду, але міняють задні деталі
            if impact_direction == "front" and any(
                rp in part_lower for rp in rear_parts
            ):
                anomalies.append(
                    f"Деталь '{part}' знаходиться ззаду, але заявлений удар був спереду ('{impact_direction}')."
                )

        if anomalies:
            return (
                "🚩 ВИЯВЛЕНО ФІЗИЧНІ НЕСТИКОВКИ В ДТП:\n"
                + "\n".join(anomalies)
                + "\nЙмовірність шахрайства: ВИСОКА."
            )
        else:
            return "✅ Фізика пошкоджень відповідає напрямку удару. Підозрілих деталей не виявлено."

    except Exception as e:
        return f"Помилка аналізу пошкоджень: {str(e)}"


@mcp.tool()
def get_current_time() -> str:
    """Повертає поточну дату та системний час."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
