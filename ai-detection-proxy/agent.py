from rules import analyze_prompt
from logger import init_logs, log_request
import requests
import json

MODEL = "qwen3:8b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_model",
            "description": "Отправляет промпт к LLM и возвращает ответ",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Промпт для модели"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "block_request",
            "description": "Блокирует запрос если он опасный",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Причина блокировки"}
                },
                "required": ["reason"]
            }
        }
    }
]

def check_rules(prompt: str) -> dict:
    """Проверяем промпт через rules.py"""
    result = analyze_prompt(prompt)
    print(f"  [tool] check_rules -> risk_score: {result['risk_score']}, rules: {[r['rule'] for r in result['triggered_rules']]}")
    return result

def call_model(prompt: str) -> str:
    """Tool 2: отправляем в Ollama"""
    response = requests.post(
        url="http://localhost:11434/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "think": False,
        }
    )
    if response.status_code == 200:
        msg = response.json()["choices"][0]["message"]
        result = msg.get("content") or msg.get("reasoning", "")
        print(f"  [tool] call_model -> получен ответ: '{result[:50]}'")
        return result
    return f"Ошибка: {response.status_code}"

def block_request(reason: str) -> str:
    """Блокируем запрос"""
    print(f"  [tool] block_request -> {reason}")
    return "Запрос заблокирован: обнаружена подозрительная активность!" 

TOOL_FUNCTIONS = {
    "call_model": call_model,
    "block_request": block_request,
}

def run_agent(user_prompt: str) -> dict:
    """Главная функция агента"""
    print(f"\n[agent] Получен промпт: {user_prompt[:50]}...")

    # принудительный check_rules всегда, независимо от модели
    analysis = check_rules(user_prompt)

    if analysis["risk_score"] >= 50:
        blocked = True
        final_response = block_request(f"risk_score: {analysis['risk_score']}")
        log_request(user_prompt, final_response, analysis, blocked)
        return {
            "response": final_response,
            "blocked": blocked,
            "analysis": analysis,
        }

    # если чисто то запуск агента для call_model
    messages = [
        {
            "role": "system",
            "content": "Ты - агент безопасности. Для каждого запроса вызови call_model и верни ответ. Не отвечай напрямую"
        },
        {"role": "user", "content": user_prompt}
    ]

    final_response = None
    blocked = False

    for step in range(5):
        response = requests.post(
            url="http://localhost:11434/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "max_tokens": 512,
                "think": False,
            }
        )

        if response.status_code != 200:
            print(f"[debug] ошибка: {response.status_code}")
            break

        message = response.json()["choices"][0]["message"]
        messages.append(message)

        if not message.get("tool_calls"):
            final_response = message.get("content", "Готово")
            break

        for tool_call in message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            # обязательно передавать оригинальный промт пользователя!
            if tool_name == "call_model":
                tool_args["prompt"] = user_prompt

            print(f"[agent] → вызов: {tool_name}")
            tool_result = TOOL_FUNCTIONS[tool_name](**tool_args)

            if tool_name == "block_request":
                blocked = True
                final_response = tool_result
            elif tool_name == "call_model":
                final_response = tool_result

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

        if final_response is not None:
            break

    log_request(user_prompt, final_response, analysis, blocked)

    return {
        "response": final_response,
        "blocked": blocked,
        "analysis": analysis,
    }

if __name__ == "__main__":
    init_logs()
    print("AI Security Agent запущен\n")
    while True:
        user_input = input(">>> ")
        if user_input.lower() == "exit":
            break
        result = run_agent(user_input)
        print(f"\nОтвет: {result['response']}")
        print(f"Заблокировано: {result['blocked']}\n")
