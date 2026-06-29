from flask import Flask, render_template_string
from logger import load_logs

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Detection Dashboard</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { color: #e94560; }
        .stats { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat-box { background: #16213e; padding: 15px 25px; border-radius: 8px; text-align: center; }
        .stat-box .number { font-size: 2em; font-weight: bold; color: #e94560; }
        .stat-box .label { font-size: 0.85em; color: #aaa; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #16213e; padding: 10px; text-align: left; color: #aaa; }
        td { padding: 10px; border-bottom: 1px solid #222; vertical-align: top; max-width: 300px; word-wrap: break-word; }
        .suspicious { background: #2a1a1a; }
        .risk-high { color: #e94560; font-weight: bold; }
        .risk-low { color: #4ecca3; }
        .rule-tag { background: #e94560; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; margin: 2px; display: inline-block; }
        .timestamp { color: #aaa; font-size: 0.8em; }
    </style>
</head>
<body>
    <h1>🛡 AI Detection Dashboard</h1>

    <div class="stats">
        <div class="stat-box">
            <div class="number">{{ total }}</div>
            <div class="label">Всего запросов</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ suspicious }}</div>
            <div class="label">Подозрительных</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ "%.0f"|format(rate) }}%</div>
            <div class="label">Attack rate</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ top_rule }}</div>
            <div class="label">Частое правило</div>
        </div>
    </div>

    <table>
        <tr>
            <th>Время</th>
            <th>Промпт</th>
            <th>Risk</th>
            <th>Правила</th>
            <th>Ответ</th>
        </tr>
        {% for log in logs %}
        <tr class="{{ 'suspicious' if log.is_suspicious else '' }}">
            <td class="timestamp">{{ log.timestamp[11:19] }}</td>
            <td>{{ log.prompt[:120] }}{{ '...' if log.prompt|length > 120 else '' }}</td>
            <td class="{{ 'risk-high' if log.risk_score > 0 else 'risk-low' }}">
                {{ log.risk_score }}
            </td>
            <td>
                {% for rule in log.triggered_rules %}
                <span class="rule-tag">{{ rule.rule }}</span>
                {% endfor %}
            </td>
            <td>{{ log.response[:150] }}{{ '...' if log.response|length > 150 else '' }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    logs = load_logs()
    logs_reversed = list(reversed(logs))

    total = len(logs)
    suspicious = sum(1 for l in logs if l["is_suspicious"])
    rate = (suspicious / total * 100) if total > 0 else 0

    # Самое частое сработавшее правило
    from collections import Counter
    all_rules = [r["rule"] for l in logs for r in l["triggered_rules"]]
    top_rule = Counter(all_rules).most_common(1)[0][0] if all_rules else "—"

    return render_template_string(
        TEMPLATE,
        logs=logs_reversed,
        total=total,
        suspicious=suspicious,
        rate=rate,
        top_rule=top_rule,
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000) 