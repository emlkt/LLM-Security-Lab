import json
import os
from datetime import datetime

LOG_FILE = "logs/requests.jsonl"

def init_logs():
    """Создаёт папку logs если её нет"""
    os.makedirs("logs", exist_ok=True)

def log_request(prompt: str, response: str, analysis: dict, blocked: bool = False):
    """Записывает один запрос в лог"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "response": response,
        "triggered_rules": [r["rule"] for r in analysis["triggered_rules"]],
        "risk_score": analysis["risk_score"],
        "is_suspicious": analysis["is_suspicious"],
        "blocked": blocked,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_logs() -> list:
    """Читает все логи из файла"""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]