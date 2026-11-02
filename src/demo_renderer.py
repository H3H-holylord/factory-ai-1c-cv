from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.cv_counter import BoundingBox, ConveyorCounter
from src.db_1c import Replica1CDatabase, UserContext


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _draw_cast_part(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int) -> None:
    draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=(92, 100, 112), outline=(145, 155, 170), width=2)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    r_outer = min(x2 - x1, y2 - y1) // 3
    r_inner = max(6, r_outer // 2)
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=(115, 124, 138), outline=(165, 175, 190), width=2)
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=(38, 42, 48), outline=(70, 76, 86), width=2)
    for bx, by in [(x1 + 12, y1 + 12), (x2 - 12, y1 + 12), (x1 + 12, y2 - 12), (x2 - 12, y2 - 12)]:
        draw.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(40, 44, 52))


def _draw_welded_bracket(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int) -> None:
    draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(84, 94, 106), outline=(150, 165, 180), width=2)
    mid_y = (y1 + y2) // 2
    draw.rectangle([x1 + 14, mid_y - 10, x2 - 14, mid_y + 10], fill=(110, 122, 136), outline=(245, 175, 65), width=2)
    draw.rectangle([x1 + 20, y1 + 12, x1 + 42, y2 - 12], fill=(102, 112, 126), outline=(245, 175, 65), width=2)
    draw.rectangle([x2 - 42, y1 + 12, x2 - 20, y2 - 12], fill=(102, 112, 126), outline=(245, 175, 65), width=2)


def generate_cv_monitoring_image(output_path: Path | str) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    conv = ConveyorCounter(line_x=430, max_match_distance=140.0)
    conv.total_count = 439
    conv.update([
        BoundingBox(380, 232, 460, 312, "Корпус ЧЛ-40", 0.99),
        BoundingBox(380, 376, 460, 456, "Корпус ЧЛ-40", 0.98),
        BoundingBox(380, 520, 460, 600, "Корпус ЧЛ-40", 0.98),
    ])
    conv_state = conv.update([
        BoundingBox(480, 232, 560, 312, "Корпус ЧЛ-40", 0.99),
        BoundingBox(480, 376, 560, 456, "Корпус ЧЛ-40", 0.98),
        BoundingBox(480, 520, 560, 600, "Корпус ЧЛ-40", 0.98),
    ])

    img = Image.new("RGB", (1600, 900), (15, 20, 28))
    draw = ImageDraw.Draw(img)

    f_title = _load_font(22, bold=True)
    f_sub = _load_font(15, bold=False)
    f_bold = _load_font(16, bold=True)
    f_small = _load_font(13, bold=False)
    f_small_b = _load_font(13, bold=True)
    f_kpi = _load_font(28, bold=True)

    # Top Header Bar
    draw.rectangle([0, 0, 1600, 68], fill=(22, 29, 41))
    draw.line([0, 68, 1600, 68], fill=(45, 62, 85), width=2)
    draw.ellipse([24, 24, 44, 44], fill=(16, 185, 129))
    draw.text((56, 14), "МОДУЛЬ КОМПЬЮТЕРНОГО ЗРЕНИЯ (YOLO11 + ByteTrack) — ПОДСЧЁТ ДЕТАЛЕЙ ОНЛАЙН", font=f_title, fill=(240, 246, 252))
    draw.text((56, 42), "Локальный сервер предприятия (On-Premise GPU)  |  Прямая запись в реплику БД 1С  |  Задержка инференса: 8.4 мс (115 FPS)", font=f_sub, fill=(148, 163, 184))

    draw.rounded_rectangle([1260, 14, 1575, 54], radius=8, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
    draw.text((1278, 24), "СТАТУС: 2/2 RTSP-ПОТОКА АКТИВНЫ", font=f_small_b, fill=(56, 189, 248))

    # ================= LEFT PANEL: CAMERA 01 (CASTING CONVEYOR) =================
    draw.rounded_rectangle([24, 88, 788, 876], radius=12, fill=(23, 31, 44), outline=(48, 64, 88), width=2)
    draw.text((44, 104), "КАМЕРА 01: ЛИТЬЁ — Конвейерная лента №1 (1–3 детали в ряд)", font=f_bold, fill=(248, 250, 252))
    draw.text((44, 128), "RTSP 1080p @ 25 FPS  |  Алгоритм: Детекция + Трекинг пересечения виртуальной линии", font=f_small, fill=(148, 163, 184))

    draw.rectangle([44, 160, 768, 670], fill=(32, 37, 46), outline=(64, 75, 92), width=2)
    draw.rectangle([46, 185, 766, 645], fill=(45, 51, 61))
    for rx in range(70, 760, 45):
        draw.line([rx, 185, rx, 645], fill=(54, 61, 73), width=2)
    draw.rectangle([46, 175, 766, 188], fill=(75, 85, 102))
    draw.rectangle([46, 642, 766, 655], fill=(75, 85, 102))

    for ax in [85, 590]:
        draw.text((ax, 405), ">>> ДВИЖЕНИЕ ЛЕНТЫ >>>", font=f_small_b, fill=(82, 94, 112))

    # Virtual Counting Line at x = 430
    line_x = 430
    draw.line([line_x, 162, line_x, 668], fill=(244, 63, 94), width=4)
    draw.rounded_rectangle([line_x - 95, 164, line_x + 95, 192], radius=6, fill=(244, 63, 94))
    draw.text((line_x - 84, 169), "ЛИНИЯ СЧЁТА (X = 430)", font=f_small_b, fill=(255, 255, 255))

    # Incoming parts (left of line)
    incoming_boxes = [
        (175, 250, 260, 335, "ID #443", "0.98"),
        (175, 485, 260, 570, "ID #444", "0.97"),
    ]
    for x1, y1, x2, y2, tid, conf in incoming_boxes:
        _draw_cast_part(draw, x1, y1, x2, y2)
        draw.rectangle([x1 - 4, y1 - 4, x2 + 4, y2 + 4], outline=(56, 189, 248), width=2)
        draw.rounded_rectangle([x1 - 4, y1 - 28, x1 + 175, y1 - 4], radius=4, fill=(14, 116, 144))
        draw.text((x1 + 4, y1 - 24), f"{tid} | В движении ({conf})", font=f_small_b, fill=(255, 255, 255))
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        draw.line([cx, cy, cx + 55, cy], fill=(56, 189, 248), width=3)

    # Counted parts (right of line, 3 in a vertical row)
    counted_ids = ["#440", "#441", "#442"]
    for idx, item in enumerate(conv_state.tracked_items):
        b = item.bbox
        _draw_cast_part(draw, b.x1, b.y1, b.x2, b.y2)
        draw.rectangle([b.x1 - 4, b.y1 - 4, b.x2 + 4, b.y2 + 4], outline=(16, 185, 129), width=3)
        draw.rounded_rectangle([b.x1 - 4, b.y1 - 28, b.x1 + 188, b.y1 - 4], radius=4, fill=(5, 150, 105))
        draw.text((b.x1 + 4, b.y1 - 24), f"ID {counted_ids[idx]} | +1 УЧТЕНО ({b.confidence})", font=f_small_b, fill=(255, 255, 255))

    # Bottom Telemetry Cards for Camera 01
    draw.rounded_rectangle([44, 688, 275, 780], radius=8, fill=(15, 23, 34), outline=(16, 185, 129), width=2)
    draw.text((60, 698), "СЧЁТЧИК КАМЕРЫ (СМЕНА)", font=f_small, fill=(148, 163, 184))
    draw.text((60, 724), f"{conv_state.total_count} шт.", font=f_kpi, fill=(16, 185, 129))

    draw.rounded_rectangle([290, 688, 520, 780], radius=8, fill=(15, 23, 34), outline=(56, 189, 248), width=1)
    draw.text((306, 698), "ДАННЫЕ 1С (ПАРТИЯ ЧЛ-40)", font=f_small, fill=(148, 163, 184))
    draw.text((306, 724), "442 шт. (100%)", font=f_kpi, fill=(240, 246, 252))

    draw.rounded_rectangle([535, 688, 768, 780], radius=8, fill=(15, 23, 34), outline=(71, 85, 105), width=1)
    draw.text((551, 698), "РЕАЛЬНАЯ ТОЧНОСТЬ", font=f_small, fill=(148, 163, 184))
    draw.text((551, 724), "99.1%", font=f_kpi, fill=(250, 204, 21))

    draw.rounded_rectangle([44, 794, 768, 858], radius=8, fill=(30, 41, 59))
    draw.text((60, 804), "Логика защиты от ошибок:", font=f_small_b, fill=(56, 189, 248))
    draw.text((60, 826), "• Одновременный трекинг 1–3 деталей в ряду (ByteTrack ID) • Защита от обратного хода и дребезга на линии", font=f_small, fill=(203, 213, 225))

    # ================= RIGHT PANEL: CAMERA 02 (WELDING ZONE) =================
    draw.rounded_rectangle([812, 88, 1576, 876], radius=12, fill=(23, 31, 44), outline=(48, 64, 88), width=2)
    draw.text((832, 104), "КАМЕРА 02: СВАРКА — Зона сдачи готовых деталей (Пост №1)", font=f_bold, fill=(248, 250, 252))
    draw.text((832, 128), "RTSP 1080p @ 25 FPS  |  Алгоритм: ROI-полигон + таймер стабилизации (фильтр рук рабочего)", font=f_small, fill=(148, 163, 184))

    draw.rectangle([832, 160, 1556, 670], fill=(35, 39, 46), outline=(64, 75, 92), width=2)
    for gx in range(860, 1550, 60):
        draw.line([gx, 162, gx, 668], fill=(45, 50, 58), width=1)
    for gy in range(190, 665, 60):
        draw.line([834, gy, 1554, gy], fill=(45, 50, 58), width=1)

    roi_x1, roi_y1, roi_x2, roi_y2 = 880, 210, 1515, 630
    draw.rounded_rectangle([roi_x1, roi_y1, roi_x2, roi_y2], radius=10, fill=(22, 48, 52), outline=(16, 185, 129), width=3)
    draw.rounded_rectangle([roi_x1 + 14, roi_y1 + 12, roi_x1 + 365, roi_y1 + 42], radius=6, fill=(16, 185, 129))
    draw.text((roi_x1 + 24, roi_y1 + 18), "ЗОНА СДАЧИ ГОТОВОЙ ДЕТАЛИ (ROI #1)", font=f_small_b, fill=(15, 23, 34))

    # Part #1 inside ROI: Confirmed
    p1_x1, p1_y1, p1_x2, p1_y2 = 915, 310, 1145, 480
    _draw_welded_bracket(draw, p1_x1, p1_y1, p1_x2, p1_y2)
    draw.rectangle([p1_x1 - 6, p1_y1 - 6, p1_x2 + 6, p1_y2 + 6], outline=(16, 185, 129), width=3)
    draw.rounded_rectangle([p1_x1 - 6, p1_y1 - 34, p1_x1 + 250, p1_y1 - 6], radius=4, fill=(5, 150, 105))
    draw.text((p1_x1 + 4, p1_y1 - 29), "ID #174: Кронштейн КР-08 [УЧТЕНО]", font=f_small_b, fill=(255, 255, 255))
    draw.rounded_rectangle([p1_x1 - 6, p1_y2 + 10, p1_x1 + 242, p1_y2 + 36], radius=4, fill=(15, 23, 34), outline=(16, 185, 129), width=1)
    draw.text((p1_x1 + 6, p1_y2 + 14), "Стабилизация: 3.0 / 3.0 сек (ОК)", font=f_small_b, fill=(16, 185, 129))

    # Part #2 being placed right now by worker
    p2_x1, p2_y1, p2_x2, p2_y2 = 1210, 310, 1440, 480
    _draw_welded_bracket(draw, p2_x1, p2_y1, p2_x2, p2_y2)
    draw.rectangle([p2_x1 - 6, p2_y1 - 6, p2_x2 + 6, p2_y2 + 6], outline=(250, 204, 21), width=3)
    draw.rounded_rectangle([p2_x1 - 6, p2_y1 - 34, p2_x1 + 265, p2_y1 - 6], radius=4, fill=(161, 98, 7))
    draw.text((p2_x1 + 4, p2_y1 - 29), "ID #175: Кронштейн КР-08 [ПРОВЕРКА]", font=f_small_b, fill=(255, 255, 255))

    # Simulated worker glove near Part #2
    gx1, gy1, gx2, gy2 = 1320, 465, 1435, 575
    draw.rounded_rectangle([gx1, gy1, gx2, gy2], radius=16, fill=(120, 85, 55), outline=(249, 115, 22), width=2)
    draw.rounded_rectangle([1195, gy2 + 6, 1502, gy2 + 34], radius=4, fill=(154, 52, 18))
    draw.text((1205, gy2 + 11), "Рука рабочего (ИГНОР — таймер 1.2 / 3.0 с)", font=f_small_b, fill=(255, 255, 255))

    # Bottom Telemetry Cards for Camera 02
    draw.rounded_rectangle([832, 688, 1063, 780], radius=8, fill=(15, 23, 34), outline=(16, 185, 129), width=2)
    draw.text((848, 698), "СДАНО НА ПОСТУ №1", font=f_small, fill=(148, 163, 184))
    draw.text((848, 724), "174 шт.", font=f_kpi, fill=(16, 185, 129))

    draw.rounded_rectangle([1078, 688, 1308, 780], radius=8, fill=(15, 23, 34), outline=(56, 189, 248), width=1)
    draw.text((1094, 698), "ДАННЫЕ 1С (ПОСТ №1)", font=f_small, fill=(148, 163, 184))
    draw.text((1094, 724), "174 шт. (100%)", font=f_kpi, fill=(240, 246, 252))

    draw.rounded_rectangle([1323, 688, 1556, 780], radius=8, fill=(15, 23, 34), outline=(71, 85, 105), width=1)
    draw.text((1339, 698), "РЕАЛЬНАЯ ТОЧНОСТЬ", font=f_small, fill=(148, 163, 184))
    draw.text((1339, 724), "97.8%", font=f_kpi, fill=(250, 204, 21))

    draw.rounded_rectangle([832, 794, 1556, 858], radius=8, fill=(30, 41, 59))
    draw.text((848, 804), "Логика защиты зоны сдачи:", font=f_small_b, fill=(56, 189, 248))
    draw.text((848, 826), "• Фиксация детали только после ухода рук рабочего и покоя > 3.0 сек • Исключение повторного счёта", font=f_small, fill=(203, 213, 225))

    img.save(out, format="PNG")
    return out


def generate_dashboard_1c_image(output_path: Path | str) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    db = Replica1CDatabase(":memory:")
    db.seed_synthetic_1c_data()
    director = UserContext(user_id=1, username="Иванов А.В. (Директор)", role="director")
    prod_rows = db.get_production_report(director)
    proc_rows = db.get_procurement_report(director)

    img = Image.new("RGB", (1600, 950), (15, 23, 36))
    draw = ImageDraw.Draw(img)

    f_title = _load_font(21, bold=True)
    f_sub = _load_font(14, bold=False)
    f_bold = _load_font(16, bold=True)
    f_small = _load_font(13, bold=False)
    f_small_b = _load_font(13, bold=True)
    f_kpi = _load_font(26, bold=True)

    # Top Navigation Header
    draw.rectangle([0, 0, 1600, 68], fill=(22, 32, 48))
    draw.line([0, 68, 1600, 68], fill=(45, 62, 85), width=2)
    draw.rounded_rectangle([20, 16, 54, 50], radius=8, fill=(56, 189, 248))
    draw.text((27, 21), "1С", font=f_bold, fill=(15, 23, 36))
    draw.text((68, 14), "ДАШБОРД ПРЕДПРИЯТИЯ + ЛОКАЛЬНЫЙ ИИ-АССИСТЕНТ (1С READ-ONLY РЕПЛИКА)", font=f_title, fill=(248, 250, 252))
    draw.text((68, 42), "Закрытый контур (без облаков)  |  Доступ: ПК и смартфоны (HTTPS / WireGuard)  |  Разграничение прав: 18 / 20 сотрудников", font=f_sub, fill=(148, 163, 184))

    # User RBAC Badge
    draw.rounded_rectangle([1195, 14, 1580, 54], radius=8, fill=(30, 41, 59), outline=(16, 185, 129), width=1)
    draw.text((1212, 25), "ПРОФИЛЬ: Иванов А.В. (Директор | 1С Read-Only)", font=f_small_b, fill=(16, 185, 129))

    # ================= KPI SUMMARY CARDS (LEFT/CENTER) =================
    kpis = [
        ("ВЫПУСК ПО 1С (СМЕНА)", "1 838 шт.", "План: 1 870 шт. (98.3%)", (56, 189, 248)),
        ("ПОДСЧЁТ КАМЕР (CV)", "1 834 шт.", "Расхождение с 1С: -4 шт.", (16, 185, 129)),
        ("АКТИВНЫЕ ЗАКУПКИ 1С", "1 981 500 ₽", "4 партии (Металл / Сырьё)", (250, 204, 21)),
        ("РЕЖИМ БАЗЫ 1С", "READ-ONLY", "Защита от записи: АКТИВНА", (168, 85, 247)),
    ]
    for i, (label, val, sub, color) in enumerate(kpis):
        x1 = 24 + i * 244
        x2 = x1 + 230
        draw.rounded_rectangle([x1, 86, x2, 192], radius=10, fill=(23, 33, 49), outline=color, width=2)
        draw.text((x1 + 16, 98), label, font=f_small_b, fill=(148, 163, 184))
        draw.text((x1 + 16, 124), val, font=f_kpi, fill=(248, 250, 252))
        draw.text((x1 + 16, 164), sub, font=f_small, fill=color)

    # ================= REPORT 1: PRODUCTION & CV RECONCILIATION =================
    draw.rounded_rectangle([24, 210, 986, 555], radius=12, fill=(23, 33, 49), outline=(48, 64, 88), width=2)
    draw.text((44, 226), "ОТЧЁТ №1: ПРОИЗВОДСТВО (Сверка выработки 1С и компьютерного зрения)", font=f_bold, fill=(248, 250, 252))
    draw.text((44, 250), "Обновление: каждые 30 сек  |  Источник: Реплика 1С:Предприятие + Сервер видеоаналитики", font=f_small, fill=(148, 163, 184))

    draw.rounded_rectangle([44, 282, 972, 318], radius=6, fill=(30, 41, 59))
    cols = [(56, "Участок / Цех"), (260, "Номенклатура (Деталь)"), (515, "План 1С"), (615, "Факт 1С"), (715, "Камера CV"), (830, "Статус сверки")]
    for cx, ctitle in cols:
        draw.text((cx, 291), ctitle, font=f_small_b, fill=(148, 163, 184))

    for idx, r in enumerate(prod_rows):
        ry = 330 + idx * 42
        if idx % 2 == 1:
            draw.rounded_rectangle([44, ry - 6, 972, ry + 30], radius=4, fill=(27, 38, 56))
        draw.text((56, ry), r["shop"], font=f_small_b, fill=(240, 246, 252))
        draw.text((260, ry), r["part_name"], font=f_small, fill=(203, 213, 225))
        draw.text((515, ry), f"{r['plan_qty']} шт.", font=f_small, fill=(148, 163, 184))
        draw.text((615, ry), f"{r['fact_qty']} шт.", font=f_small_b, fill=(240, 246, 252))
        draw.text((715, ry), f"{r['cv_qty']} шт.", font=f_small_b, fill=(56, 189, 248))

        diff = r["discrepancy"]
        if diff == 0:
            draw.rounded_rectangle([825, ry - 2, 968, ry + 24], radius=6, fill=(6, 78, 59))
            draw.text((838, ry + 2), "[OK] Точно (0)", font=f_small_b, fill=(52, 211, 153))
        else:
            draw.rounded_rectangle([825, ry - 2, 968, ry + 24], radius=6, fill=(120, 53, 15))
            draw.text((834, ry + 2), f"[!] -{diff} шт. (Сверка)", font=f_small_b, fill=(251, 191, 36))

    # ================= REPORT 2: PROCUREMENT & INVENTORY (1C) =================
    draw.rounded_rectangle([24, 575, 986, 926], radius=12, fill=(23, 33, 49), outline=(48, 64, 88), width=2)
    draw.text((44, 591), "ОТЧЁТ №2: ЗАКУПКИ И СНАБЖЕНИЕ (Металлопрокат, литейный чугун, расходники)", font=f_bold, fill=(248, 250, 252))
    draw.text((44, 615), "Доступ ограничен ролями: Директор, Отдел снабжения (RBAC фильтр)", font=f_small, fill=(148, 163, 184))

    draw.rounded_rectangle([44, 646, 972, 682], radius=6, fill=(30, 41, 59))
    pcols = [(56, "Материал / Сырьё"), (330, "Поставщик"), (555, "Объём (т)"), (665, "Сумма (₽)"), (805, "Статус / Поставка")]
    for cx, ctitle in pcols:
        draw.text((cx, 655), ctitle, font=f_small_b, fill=(148, 163, 184))

    for idx, r in enumerate(proc_rows):
        ry = 696 + idx * 48
        if idx % 2 == 1:
            draw.rounded_rectangle([44, ry - 6, 972, ry + 34], radius=4, fill=(27, 38, 56))
        draw.text((56, ry), r["material"], font=f_small_b, fill=(240, 246, 252))
        draw.text((330, ry), r["supplier"], font=f_small, fill=(203, 213, 225))
        draw.text((555, ry), f"{r['weight_tons']} т", font=f_small, fill=(203, 213, 225))
        amt = f"{r['amount_rub']:,} ₽".replace(",", " ")
        draw.text((665, ry), amt, font=f_small_b, fill=(250, 204, 21))
        draw.text((805, ry), f"{r['status']} ({r['delivery_date']})", font=f_small_b, fill=(56, 189, 248))

    # ================= RIGHT PANEL: LOCAL AI CHAT (OPEN WEBUI / QWEN 2.5) =================
    draw.rounded_rectangle([1006, 86, 1576, 926], radius=12, fill=(19, 28, 42), outline=(56, 189, 248), width=2)
    draw.rounded_rectangle([1008, 88, 1574, 154], radius=10, fill=(26, 38, 58))
    draw.text((1028, 98), "[ИИ] ЛОКАЛЬНЫЙ ЧАТ С НЕЙРОСЕТЬЮ (Qwen 2.5 + 1С SQL)", font=f_bold, fill=(248, 250, 252))
    draw.text((1028, 124), "Модель: Qwen2.5-32B-Instruct (Локально)  |  Штат: 15–20 сотрудников", font=f_small, fill=(56, 189, 248))

    # User message bubble
    draw.rounded_rectangle([1080, 170, 1554, 236], radius=10, fill=(37, 99, 235))
    draw.text((1096, 180), "Иванов А.В. (Директор) — со смартфона:", font=f_small_b, fill=(191, 219, 254))
    draw.text((1096, 204), "Покажи сверку выработки 1С и камер за смену. Где расхождения?", font=f_small, fill=(255, 255, 255))

    # AI SQL execution badge
    draw.rounded_rectangle([1028, 250, 1554, 304], radius=8, fill=(15, 23, 34), outline=(71, 85, 105), width=1)
    draw.text((1042, 258), "[SQL] Выполнено к Read-Only реплике 1С (безопасный SELECT):", font=f_small_b, fill=(16, 185, 129))
    draw.text((1042, 280), "SELECT shop, part_name, fact_qty, cv_qty FROM production_batches;", font=f_small, fill=(148, 163, 184))

    # AI Answer Bubble
    draw.rounded_rectangle([1028, 318, 1554, 592], radius=10, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
    draw.text((1046, 330), "Ответ нейросети (по данным 1С и CV):", font=f_small_b, fill=(56, 189, 248))

    summary_lines = [
        ("Сводка за смену: по 1С = 1 838 шт. | по камерам CV = 1 834 шт.", (240, 246, 252)),
        ("• Литьё №1 (Корпус ЧЛ-40): 1С = 442 | CV = 442 шт. (100% точно)", (52, 211, 153)),
        ("• Литьё №2 (Фланец ФС-120): 1С = 785 | CV = 784 шт. (-1 шт.)", (251, 191, 36)),
        ("• Сварка Пост №1 (Кронштейн КР-08): 1С = 174 | CV = 174 шт. (100%)", (52, 211, 153)),
        ("• Сварка Пост №2 (Балка БО-24): 1С = 118 | CV = 115 шт. (-3 шт.)", (251, 191, 36)),
        ("• ЧПУ (Вал ВП-16): 1С = 319 | CV = 319 шт. (100% точно)", (52, 211, 153)),
        ("Рекомендация: проверить 3 детали БО-24 на Посту сварки №2.", (56, 189, 248)),
    ]
    y_cursor = 362
    for text_line, col in summary_lines:
        draw.text((1046, y_cursor), text_line, font=f_small, fill=col)
        y_cursor += 31

    # Second User Question (Procurement RBAC demo)
    draw.rounded_rectangle([1080, 610, 1554, 674], radius=10, fill=(37, 99, 235))
    draw.text((1096, 618), "Иванов А.В. (Директор):", font=f_small_b, fill=(191, 219, 254))
    draw.text((1096, 642), "Что по закупкам чугуна и стали 09Г2С на этой неделе?", font=f_small, fill=(255, 255, 255))

    draw.rounded_rectangle([1028, 690, 1554, 845], radius=10, fill=(30, 41, 59), outline=(16, 185, 129), width=1)
    draw.text((1046, 702), "Ответ нейросети (Отдел снабжения 1С):", font=f_small_b, fill=(16, 185, 129))
    draw.text((1046, 728), "• Чугун литейный ПЛ-1 (18.5 т) — 647 500 ₽: Уже на складе.", font=f_small, fill=(240, 246, 252))
    draw.text((1046, 754), "• Сталь 09Г2С 12мм (12.0 т) — 912 000 ₽: В пути (ожид. 03.11).", font=f_small, fill=(240, 246, 252))
    draw.text((1046, 780), "• Проволока СВ-08Г2С (1.4 т) — 238 000 ₽: Оплачено (04.11).", font=f_small, fill=(240, 246, 252))
    draw.text((1046, 810), "[RBAC OK] Права доступа подтверждены (Роль: Директор).", font=f_small_b, fill=(148, 163, 184))

    # Chat Input Box at Bottom
    draw.rounded_rectangle([1028, 862, 1554, 908], radius=8, fill=(15, 23, 34), outline=(71, 85, 105), width=1)
    draw.text((1046, 876), "Задайте вопрос по базе 1С, производству или камерам...", font=f_small, fill=(100, 116, 139))

    img.save(out, format="PNG")
    return out
