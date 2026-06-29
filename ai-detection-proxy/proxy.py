import requests
from rules import analyze_prompt
from logger import init_logs, log_request
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()

"""
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "meta-llama/llama-3.3-70b-instruct:free"
"""
MODEL = "qwen3:8b"
RISK_THRESHOLD = 50  # порог блокировки

def query_llm(prompt: str) -> str:
    """Отправляет промпт к модели"""
    response = requests.post(
        #url="https://openrouter.ai/api/v1/chat/completions",
        url="http://localhost:11434/v1/chat/completions",
        headers={
            #"Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256,
        }
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка: {response.status_code}"

def process_request(prompt: str) -> dict:
    """
    Главная функция это прослойка между пользователем и LLM.
    Анализирует промпт, блокирует если опасно, логирует.
    """
    analysis = analyze_prompt(prompt)
    blocked = False
    response = None

    if analysis["risk_score"] >= RISK_THRESHOLD:
        blocked = True
        response = "Запрос заблокирован: обнаружена подозрительная активность."
        print(f"🚫 ЗАБЛОКИРОВАНО. Risk score: {analysis['risk_score']}")
    else:
        if analysis["is_suspicious"]:
            print(f"⚠️  Подозрительно, но пропускаем. Risk score: {analysis['risk_score']}")
        response = query_llm(prompt)

    log_request(prompt, response, analysis, blocked)

    return {
        "response": response,
        "analysis": analysis,
        "blocked": blocked,
    }

if __name__ == "__main__":
    init_logs()
    print("AI Detection Proxy запущен. Введите промпт (или 'exit' для выхода):\n")
    while True:
        user_input = input(">>> ")
        if user_input.lower() == "exit":
            break
        result = process_request(user_input)
        print(f"\nОтвет: {result['response']}")
        print(f"Risk score: {result['analysis']['risk_score']}")
        print(f"Заблокировано: {result['blocked']}\n")