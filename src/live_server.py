from aiohttp import web
from src.db_1c import (
    AccessDeniedError,
    ReadOnlyViolationError,
    Replica1CDatabase,
    UserContext,
    answer_employee_question,
)

ROLE_USERS = {
    "director": UserContext(1, "Иванов А.В. (Директор)", "director"),
    "production": UserContext(2, "Петров С.Н. (Начальник цеха)", "production"),
    "procurement": UserContext(3, "Сидорова Е.М. (Отдел закупок)", "procurement"),
}

INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ДАШБОРД ПРЕДПРИЯТИЯ + КОМПЬЮТЕРНОЕ ЗРЕНИЕ + 1С (Демо-стенд)</title>
<style>
  :root {
    --bg: #0f1724;
    --card: #172133;
    --border: #2d3e55;
    --cyan: #38bdf8;
    --green: #10b981;
    --yellow: #facc15;
    --red: #f43f5e;
    --text: #f8fafc;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
  body { background: var(--bg); color: var(--text); padding-bottom: 40px; }
  header {
    background: #162030; border-bottom: 2px solid var(--border);
    padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .badge-1c { background: var(--cyan); color: #0f1724; font-weight: 800; padding: 6px 10px; border-radius: 8px; }
  .role-box { display: flex; align-items: center; gap: 10px; background: #1e293b; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--green); }
  select { background: #0f1724; color: var(--green); border: 1px solid var(--border); padding: 6px 10px; border-radius: 6px; font-weight: 600; cursor: pointer; }
  .container { max-width: 1560px; margin: 18px auto; padding: 0 20px; display: grid; grid-template-columns: 1.55fr 1fr; gap: 20px; }
  @media (max-width: 1100px) { .container { grid-template-columns: 1fr; } }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 18px; }
  .card-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
  .card-sub { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
  .cv-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 768px) { .cv-grid { grid-template-columns: 1fr; } }
  canvas { width: 100%; height: 250px; background: #1e242d; border-radius: 8px; border: 1px solid #3f4b5e; display: block; }
  .btn-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  button {
    background: #1e293b; color: var(--text); border: 1px solid var(--cyan);
    padding: 7px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; transition: 0.15s;
  }
  button:hover { background: var(--cyan); color: #0f1724; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th { text-align: left; padding: 10px 8px; background: #1e293b; color: var(--muted); font-weight: 600; }
  td { padding: 10px 8px; border-bottom: 1px solid #243247; }
  .pill-ok { background: #064e3b; color: #34d399; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 12px; }
  .pill-warn { background: #78350f; color: #fbbf24; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 12px; }
  .chat-box { height: 470px; overflow-y: auto; padding: 12px; background: #0f1724; border-radius: 8px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; }
  .msg-user { align-self: flex-end; background: #2563eb; color: #fff; padding: 10px 14px; border-radius: 10px; max-width: 85%; font-size: 13.5px; }
  .msg-ai { align-self: flex-start; background: #1e293b; border: 1px solid var(--cyan); padding: 12px 14px; border-radius: 10px; max-width: 92%; font-size: 13.5px; white-space: pre-line; }
  .sql-tag { font-family: Consolas, monospace; font-size: 12px; color: var(--green); background: #0b111c; padding: 6px 8px; border-radius: 6px; margin-bottom: 6px; display: block; }
  .chat-input-row { display: flex; gap: 8px; margin-top: 12px; }
  input[type="text"] { flex: 1; background: #0f1724; color: #fff; border: 1px solid var(--border); padding: 10px 12px; border-radius: 8px; font-size: 14px; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge-1c">1С + CV</span>
    <div>
      <div style="font-size:18px; font-weight:700;">ДАШБОРД ПРЕДПРИЯТИЯ + ЛОКАЛЬНАЯ НЕЙРОСЕТЬ + КОМПЬЮТЕРНОЕ ЗРЕНИЕ</div>
      <div style="font-size:13px; color:var(--muted);">Живой интерактивный демо-стенд (100% локально, без облаков, 1С Read-Only)</div>
    </div>
  </div>
  <div class="role-box">
    <span style="font-size:13px; color:var(--muted);">Роль сотрудника (RBAC):</span>
    <select id="roleSelect" onchange="loadState()">
      <option value="director">Иванов А.В. — Директор (Полный доступ)</option>
      <option value="production">Петров С.Н. — Начальник цеха (Только производство)</option>
      <option value="procurement">Сидорова Е.М. — Снабжение (Только закупки)</option>
    </select>
  </div>
</header>

<div class="container">
  <div>
    <!-- БЛОК ВИДЕОАНАЛИТИКИ -->
    <div class="card">
      <div class="card-title">
        <span>МОДУЛЬ КОМПЬЮТЕРНОГО ЗРЕНИЯ (Онлайн-симуляция камер)</span>
        <span style="color:var(--green); font-size:13px;">● 2/2 RTSP-потока активны</span>
      </div>
      <div class="card-sub">Детали автоматически считаются при пересечении линии (литьё) и после 3 сек стабилизации в зоне сдачи (сварка)</div>
      <div class="cv-grid">
        <div>
          <div style="font-size:14px; font-weight:600; margin-bottom:6px;">Камера 01: Литьё (1–3 детали в ряд на ленте)</div>
          <canvas id="camConveyor" width="520" height="250"></canvas>
          <div class="btn-row">
            <button onclick="spawnConveyorRow(3)">+ Пустить 3 детали в ряд</button>
            <button onclick="spawnConveyorRow(2)">+ Пустить 2 детали в ряд</button>
          </div>
        </div>
        <div>
          <div style="font-size:14px; font-weight:600; margin-bottom:6px;">Камера 02: Сварка (Зона сдачи + фильтр рук)</div>
          <canvas id="camWelding" width="520" height="250"></canvas>
          <div class="btn-row">
            <button onclick="placeWeldedPart()">+ Положить готовую деталь (3с)</button>
            <button onclick="triggerWorkerHand()" style="border-color:var(--yellow);">Рука рабочего (Игнор &lt; 3с)</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ОТЧЁТ 1: ПРОИЗВОДСТВО -->
    <div class="card">
      <div class="card-title">ОТЧЁТ №1: ПРОИЗВОДСТВО (Сверка выработки 1С и камер CV)</div>
      <div class="card-sub">Каждая посчитанная на камерах деталь в реальном времени обновляет столбец «Камера CV»</div>
      <div id="prodContainer"></div>
    </div>

    <!-- ОТЧЁТ 2: ЗАКУПКИ -->
    <div class="card">
      <div class="card-title">ОТЧЁТ №2: ЗАКУПКИ И СНАБЖЕНИЕ (Из копии 1С Read-Only)</div>
      <div class="card-sub">Проверка разграничения прав: переключите роль вверху на «Начальник цеха», чтобы увидеть блокировку</div>
      <div id="procContainer"></div>
    </div>
  </div>

  <!-- ПРАВАЯ КОЛОНКА: ИИ-ЧАТ -->
  <div>
    <div class="card" style="border-color:var(--cyan);">
      <div class="card-title">[ИИ] ЛОКАЛЬНЫЙ ЧАТ С НЕЙРОСЕТЬЮ (Qwen 2.5 + 1С SQL)</div>
      <div class="card-sub">Нейросеть переводит вопрос в безопасный SELECT-запрос к Read-Only копии 1С с учётом роли сотрудника</div>
      <div class="btn-row" style="margin-bottom:10px;">
        <button onclick="sendQuick('Покажи сверку выработки 1С и камер за смену')">Сверка 1С и камер</button>
        <button onclick="sendQuick('Что по закупкам чугуна и стали на этой неделе?')">Отчёт по закупкам</button>
        <button onclick="sendQuick('DELETE FROM production_batches')" style="border-color:var(--red); color:#fda4af;">Тест взлома (DELETE)</button>
      </div>
      <div class="chat-box" id="chatBox"></div>
      <div class="chat-input-row">
        <input type="text" id="chatInput" placeholder="Задайте вопрос по базе 1С, литью, сварке или закупкам..." onkeydown="if(event.key==='Enter') sendChat()">
        <button onclick="sendChat()" style="background:var(--cyan); color:#0f1724;">Отправить</button>
      </div>
    </div>
  </div>
</div>

<script>
let conveyorParts = [
  {x: 80, y: 45, id: 443, counted: false},
  {x: 80, y: 120, id: 444, counted: false},
  {x: 80, y: 195, id: 445, counted: false}
];
let nextTrackId = 446;
let weldingState = { status: 'confirmed', timer: 3.0, id: 174 };

async function loadState() {
  const role = document.getElementById('roleSelect').value;
  const res = await fetch('/api/state?role=' + role);
  const data = await res.json();

  // Render Production
  if (data.production_restricted) {
    document.getElementById('prodContainer').innerHTML = `<div style="padding:14px; background:#3b1824; border:1px solid var(--red); border-radius:8px; color:#fda4af;">🔒 Доступ ограничен ролью: Сотрудник отдела закупок не видит производственную выработку цехов.</div>`;
  } else {
    let rows = data.production.map(r => {
      const badge = r.discrepancy === 0
        ? `<span class="pill-ok">[OK] Точно (0)</span>`
        : `<span class="pill-warn">[!] Δ ${r.discrepancy > 0 ? '-' + r.discrepancy : '+' + Math.abs(r.discrepancy)} шт.</span>`;
      return `<tr><td><b>${r.shop}</b></td><td>${r.part_name}</td><td>${r.plan_qty} шт.</td><td><b>${r.fact_qty} шт.</b></td><td style="color:var(--cyan); font-weight:700;">${r.cv_qty} шт.</td><td>${badge}</td></tr>`;
    }).join('');
    document.getElementById('prodContainer').innerHTML = `<table><thead><tr><th>Участок</th><th>Деталь</th><th>План 1С</th><th>Факт 1С</th><th>Камера CV</th><th>Сверка</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  // Render Procurement
  if (data.procurement_restricted) {
    document.getElementById('procContainer').innerHTML = `<div style="padding:14px; background:#3b1824; border:1px solid var(--red); border-radius:8px; color:#fda4af;">🔒 Доступ ограничен (RBAC): Роль «Начальник цеха» не имеет доступа к финансовым закупкам и ценам поставщиков.</div>`;
  } else {
    let rows = data.procurement.map(r => `<tr><td><b>${r.material}</b></td><td>${r.supplier}</td><td>${r.weight_tons} т</td><td style="color:var(--yellow); font-weight:700;">${r.amount_rub.toLocaleString('ru-RU')} ₽</td><td style="color:var(--cyan);">${r.status} (${r.delivery_date})</td></tr>`).join('');
    document.getElementById('procContainer').innerHTML = `<table><thead><tr><th>Материал</th><th>Поставщик</th><th>Объём</th><th>Сумма</th><th>Статус</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
}

async function incrementServerCounter(shopPrefix, delta) {
  await fetch('/api/cv_increment', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({shop_prefix: shopPrefix, delta: delta})
  });
  loadState();
}

function spawnConveyorRow(count) {
  const ys = count === 3 ? [45, 120, 195] : [75, 165];
  ys.forEach(y => conveyorParts.push({x: 30, y: y, id: nextTrackId++, counted: false}));
}

function placeWeldedPart() {
  weldingState = { status: 'checking', timer: 0.1, id: weldingState.id + 1 };
}

function triggerWorkerHand() {
  weldingState = { status: 'hand', timer: 0.8, id: weldingState.id };
}

function animateCV() {
  // 1. Conveyor Canvas
  const c1 = document.getElementById('camConveyor');
  const ctx1 = c1.getContext('2d');
  ctx1.fillStyle = '#252b34';
  ctx1.fillRect(0, 0, c1.width, c1.height);

  // Rollers
  ctx1.strokeStyle = '#333b48';
  for (let x = 20; x < c1.width; x += 40) {
    ctx1.beginPath(); ctx1.moveTo(x, 15); ctx1.lineTo(x, 235); ctx1.stroke();
  }
  // Virtual Line at x=300
  ctx1.strokeStyle = '#f43f5e'; ctx1.lineWidth = 3;
  ctx1.beginPath(); ctx1.moveTo(300, 0); ctx1.lineTo(300, 250); ctx1.stroke();
  ctx1.fillStyle = '#f43f5e'; ctx1.fillRect(230, 6, 140, 20);
  ctx1.fillStyle = '#fff'; ctx1.font = 'bold 11px Segoe UI';
  ctx1.fillText('ЛИНИЯ СЧЁТА (X=300)', 240, 20);

  let newlyCounted = 0;
  conveyorParts.forEach(p => {
    p.x += 1.4;
    if (!p.counted && p.x >= 300) {
      p.counted = true;
      newlyCounted++;
    }
    ctx1.fillStyle = '#5c6675';
    ctx1.fillRect(p.x - 22, p.y - 22, 44, 44);
    ctx1.strokeStyle = p.counted ? '#10b981' : '#38bdf8';
    ctx1.lineWidth = 2;
    ctx1.strokeRect(p.x - 25, p.y - 25, 50, 50);
    ctx1.fillStyle = p.counted ? '#059669' : '#0e7490';
    ctx1.fillRect(p.x - 25, p.y - 42, 118, 16);
    ctx1.fillStyle = '#fff'; ctx1.font = 'bold 10px Segoe UI';
    ctx1.fillText(`#${p.id} ${p.counted ? '+1 УЧТЕНО' : 'Движение'}`, p.x - 21, p.y - 30);
  });
  if (newlyCounted > 0) incrementServerCounter('Литьё (Линия №1)', newlyCounted);
  conveyorParts = conveyorParts.filter(p => p.x < 560);
  if (conveyorParts.length === 0) spawnConveyorRow(3);

  // 2. Welding Zone Canvas
  const c2 = document.getElementById('camWelding');
  const ctx2 = c2.getContext('2d');
  ctx2.fillStyle = '#23272f';
  ctx2.fillRect(0, 0, c2.width, c2.height);

  // ROI Polygon
  ctx2.strokeStyle = '#10b981'; ctx2.lineWidth = 2;
  ctx2.strokeRect(40, 30, 440, 195);
  ctx2.fillStyle = '#10b981'; ctx2.fillRect(50, 38, 230, 20);
  ctx2.fillStyle = '#0f1724'; ctx2.font = 'bold 11px Segoe UI';
  ctx2.fillText('ЗОНА СДАЧИ СВАРКИ (ROI #1)', 58, 52);

  if (weldingState.status === 'checking') {
    weldingState.timer += 0.025;
    if (weldingState.timer >= 3.0) {
      weldingState.timer = 3.0;
      weldingState.status = 'confirmed';
      incrementServerCounter('Сварка (Пост №1)', 1);
    }
  } else if (weldingState.status === 'hand') {
    weldingState.timer += 0.025;
    if (weldingState.timer >= 2.2) {
      weldingState.status = 'confirmed';
      weldingState.timer = 3.0;
    }
  }

  // Draw part in zone
  ctx2.fillStyle = '#556070';
  ctx2.fillRect(150, 85, 210, 95);
  const isOk = weldingState.status === 'confirmed';
  ctx2.strokeStyle = isOk ? '#10b981' : '#facc15';
  ctx2.lineWidth = 3;
  ctx2.strokeRect(145, 80, 220, 105);
  ctx2.fillStyle = isOk ? '#059669' : '#a16207';
  ctx2.fillRect(145, 58, 220, 20);
  ctx2.fillStyle = '#fff'; ctx2.font = 'bold 11px Segoe UI';
  ctx2.fillText(
    isOk
      ? `ID #${weldingState.id}: ЗАФИКСИРОВАНО (3.0/3.0с)`
      : (weldingState.status === 'hand' ? 'РУКА РАБОЧЕГО В КАДРЕ — ИГНОР!' : `Стабилизация: ${weldingState.timer.toFixed(1)} / 3.0 сек...`),
    152, 72
  );

  requestAnimationFrame(animateCV);
}

async function sendQuick(text) {
  document.getElementById('chatInput').value = text;
  await sendChat();
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const q = input.value.trim();
  if (!q) return;
  input.value = '';

  const role = document.getElementById('roleSelect').value;
  const box = document.getElementById('chatBox');
  box.innerHTML += `<div class="msg-user">${q}</div>`;

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({role: role, question: q})
  });
  const data = await res.json();
  box.innerHTML += `<div class="msg-ai"><span class="sql-tag">[SQL] ${data.generated_sql}</span>${data.answer}</div>`;
  box.scrollTop = box.scrollHeight;
}

window.onload = () => {
  loadState();
  sendQuick('Покажи сверку выработки 1С и камер за смену');
  requestAnimationFrame(animateCV);
};
</script>
</body>
</html>
"""


def create_app() -> web.Application:
    db = Replica1CDatabase(":memory:")
    db.seed_synthetic_1c_data()

    async def handle_index(request: web.Request) -> web.Response:
        return web.Response(text=INDEX_HTML, content_type="text/html")

    async def handle_state(request: web.Request) -> web.Response:
        role = request.query.get("role", "director")
        user = ROLE_USERS.get(role, ROLE_USERS["director"])

        prod_rows = []
        prod_restricted = False
        try:
            prod_rows = db.get_production_report(user)
        except AccessDeniedError:
            prod_restricted = True

        proc_rows = []
        proc_restricted = False
        try:
            proc_rows = db.get_procurement_report(user)
        except AccessDeniedError:
            proc_restricted = True

        return web.json_response(
            {
                "role": user.role,
                "username": user.username,
                "production": prod_rows,
                "production_restricted": prod_restricted,
                "procurement": proc_rows,
                "procurement_restricted": proc_restricted,
            }
        )

    async def handle_chat(request: web.Request) -> web.Response:
        body = await request.json()
        role = body.get("role", "director")
        question = body.get("question", "")
        user = ROLE_USERS.get(role, ROLE_USERS["director"])

        try:
            if any(k in question.upper() for k in ("DELETE", "DROP", "UPDATE", "INSERT")):
                db.execute_readonly_query(question)
            reply = answer_employee_question(db=db, user=user, question=question)
            return web.json_response(
                {
                    "generated_sql": reply.generated_sql,
                    "answer": reply.answer,
                }
            )
        except ReadOnlyViolationError as exc:
            return web.json_response(
                {
                    "generated_sql": f"ЗАБЛОКИРОВАНО: {question}",
                    "answer": f"🛡️ Защита Read-Only реплики 1С: Модификация данных запрещена! ({exc})",
                }
            )
        except AccessDeniedError as exc:
            return web.json_response(
                {
                    "generated_sql": "RBAC ACCESS DENIED",
                    "answer": f"🔒 Отказ в доступе по роли ({user.username}): У вас нет прав на просмотр этого раздела 1С ({exc}).",
                }
            )

    async def handle_cv_increment(request: web.Request) -> web.Response:
        body = await request.json()
        shop_prefix = body.get("shop_prefix", "Литьё (Линия №1)")
        delta = int(body.get("delta", 1))
        db.conn.execute(
            "UPDATE production_batches SET cv_qty = cv_qty + ?, fact_qty = fact_qty + ? WHERE shop = ?",
            (delta, delta, shop_prefix),
        )
        db.conn.commit()
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/state", handle_state)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/cv_increment", handle_cv_increment)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="127.0.0.1", port=8080)
