# -*- coding: utf-8 -*-
"""Builder: megaproject scenario model workbook (50 projects + valuation scenarios).

All amounts in $ billions unless noted. Live formulas everywhere; inputs are
blue (finance convention), cross-sheet refs green.
"""
import sys, os

XLSX_SKILL_DIR = r"C:\Users\ilayl\.zcode\cli\plugins\cache\zcode-plugins-official\spreadsheets\0.2.2\skills\xlsx"
for sub in [XLSX_SKILL_DIR, os.path.join(XLSX_SKILL_DIR, "templates")]:
    if sub not in sys.path:
        sys.path.insert(0, sub)

from base import *  # noqa: F401,F403 - design tokens & helpers
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import Reference

use_palette_explicit("professional")

OUT = r"C:\Users\ilayl\.zcode\workspace\draft-971855dc-c646-4cf9-8dbd-23622abc83ec\megaproject_model.xlsx"


from openpyxl.worksheet.properties import PageSetupProperties


def setup_print(ws, fit_height=0):
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = fit_height
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)

R_AZIA, R_SA, R_EU, R_AM = "Азия ЮВ", "Юж. Азия/БВ", "Европа/Турция", "Америка/Океания"

# (no, region, name, capex_min, capex_max, rev_min, rev_max,
#  real_capex_min, real_capex_max, real_rev_min, real_rev_max, class)
ITEMS = [
    (1,  R_AZIA, "Тоннель Корея — Япония (Пусан — Кюсю)", 50, 80, 3.5, 6.0, 70, 120, 1.0, 2.0, "D"),
    (2,  R_AZIA, "Тоннель через Тайваньский пролив", 40, 60, 3.5, 5.0, 60, 100, 1.5, 3.0, "D"),
    (3,  R_AZIA, "Канал Кра (Таиланд)", 30, 50, 3.0, 5.0, 28, 50, 1.5, 2.5, "C"),
    (4,  R_AZIA, "Тоннель под Бохайским заливом (Далянь — Яньтай)", 35, 40, 3.0, 4.0, 43, 60, 1.8, 3.0, "B"),
    (5,  R_AZIA, "Тоннель Хайнань — материк (пролив Цюнчжоу)", 20, 25, 1.8, 2.8, 20, 28, 0.9, 1.5, "B"),
    (6,  R_AZIA, "Переход через Малаккский пролив (Малайзия — Суматра)", 12, 15, 1.5, 2.5, 13, 20, 0.8, 1.5, "C"),
    (7,  R_AZIA, "Переход через Зондский пролив (Ява — Суматра)", 15, 18, 1.5, 2.0, 10, 20, 0.7, 1.2, "B"),
    (8,  R_AZIA, "Сеть переходов на Филиппинах (Лусон — Самар — Лейте — Минданао)", 10, 15, 1.2, 2.0, 12, 18, 0.6, 1.0, "B"),
    (9,  R_AZIA, "Мост через Манильский залив (Батаан — Кавите)", 3.0, 3.5, 0.40, 0.60, 4.0, 4.5, 0.15, 0.30, "A"),
    (10, R_AZIA, "Тоннель Токийский залив — 2 (Аква-Лайн-2)", 10, 14, 1.1, 1.6, 10, 15, 0.15, 0.40, "B"),
    (11, R_AZIA, "Мост Шэньчжэнь — Чжухай (дельта Жемчужной реки)", 7, 10, 1.0, 1.5, 7, 9, 0.60, 1.20, "A"),
    (12, R_AZIA, "Мост Сингапур — остров Батам", 5, 8, 0.9, 1.4, 6, 10, 0.4, 0.8, "C"),
    (13, R_AZIA, "Переход на остров Чеджу, этап 1", 4.0, 6.0, 0.60, 0.85, 8.0, 12.0, 0.25, 0.45, "C"),
    (14, R_AZIA, "Переход на остров Чеджу, этап 2", 3.5, 5.5, 0.45, 0.70, 7.0, 8.0, 0.15, 0.25, "C"),
    (15, R_AZIA, "Тоннель Нинбо — Чжоушань (залив Ханчжоувань-2)", 4, 6, 0.6, 0.9, 4, 7, 0.4, 0.7, "A"),
    (16, R_AZIA, "Мост Джава — Бали", 1.2, 1.8, 0.18, 0.28, 1.2, 1.8, 0.09, 0.14, "B"),
    (17, R_AZIA, "Мост Батам — Бинтан (Индонезия)", 0.8, 1.2, 0.12, 0.18, 0.8, 1.2, 0.06, 0.09, "B"),
    (18, R_AZIA, "Переход на остров Пхукет (Таиланд)", 0.9, 1.4, 0.15, 0.25, 0.9, 1.4, 0.075, 0.125, "B"),
    (19, R_AZIA, "Мост на остров Фукуок (Вьетнам)", 0.5, 1.0, 0.15, 0.23, 0.5, 1.0, 0.075, 0.115, "C"),
    (20, R_SA, "Сухопутный коридор Хайфа — Персидский залив (IMEC)", 15, 22, 1.5, 2.5, 15, 25, 0.6, 1.2, "C"),
    (21, R_SA, "Баб-эль-Мандебский переход (Йемен — Джибути)", 10, 15, 1.5, 2.0, 20, 40, 0.3, 0.8, "D"),
    (22, R_SA, "Подводный тоннель Дубай — Доха", 12, 18, 1.2, 1.8, 15, 25, 0.7, 1.3, "B"),
    (23, R_SA, "Мост Египет — Саудовская Аравия (пролив Тиран)", 4, 7, 0.8, 1.2, 8, 12, 0.3, 0.6, "C"),
    (24, R_SA, "Коридор Калькутта — Дакка / мост Падма-2", 4, 6, 0.6, 0.9, 4, 6, 0.15, 0.30, "C"),
    (25, R_SA, "Адамов мост (Индия — Шри-Ланка)", 4.5, 5.0, 0.5, 0.8, 6, 9, 0.2, 0.4, "D"),
    (26, R_SA, "Второй трансморской мост Мумбаи — Алибаг", 3.0, 4.5, 0.5, 0.8, 2.5, 4.0, 0.15, 0.30, "A"),
    (27, R_SA, "Мост Браззавиль — Киншаса", 0.8, 1.2, 0.20, 0.35, 0.8, 1.2, 0.03, 0.08, "B"),
    (28, R_EU, "Второй Евротоннель под Ла-Маншем", 18, 25, 1.8, 2.5, 40, 60, 1.2, 1.8, "C"),
    (29, R_EU, "Канал «Стамбул» (дублёр Босфора)", 15, 20, 1.5, 2.0, 20, 65, 0.10, 0.30, "C"),
    (30, R_EU, "Тоннель Мон-Сени (Франция — Италия, TELT)", 12, 15, 1.0, 1.5, 11, 13, 0.3, 0.6, "A"),
    (31, R_EU, "Тоннель под Гибралтарским проливом", 8, 12, 0.9, 1.6, 9, 15, 0.3, 0.7, "B"),
    (32, R_EU, "Тоннель Хельсинки — Таллинн (FinEst Link)", 15, 20, 0.7, 1.6, 13, 20, 0.4, 0.8, "C"),
    (33, R_EU, "Тоннель Великобритания — Ирландия", 24, 38, 0.6, 1.2, 260, 420, 0.3, 0.6, "D"),
    (34, R_EU, "Переход через пролив Каттегат (Хельсингёр — Хельсингборг)", 10, 14, 0.8, 1.2, 6, 8, 0.3, 0.6, "C"),
    (35, R_EU, "Мессинский висячий мост (Италия — Сицилия)", 14, 15, 0.8, 1.0, 14, 16, 0.25, 0.40, "A"),
    (36, R_EU, "Большой трёхуровневый Стамбульский тоннель", 4, 6, 0.6, 1.0, 3.5, 5.0, 0.3, 0.5, "B"),
    (37, R_EU, "Северный обход Стамбула / мост Измит (остаток)", 3.0, 4.5, 0.5, 0.8, 1.0, 2.0, 0.3, 0.5, "A"),
    (38, R_EU, "Переход на остров Крит (Пелопоннес — Китира — Крит)", 6, 9, 0.4, 0.6, 7, 12, 0.15, 0.30, "C"),
    (39, R_EU, "Дублёр тоннеля Осло-фьорд (Норвегия)", 0.8, 1.2, 0.08, 0.12, 1.2, 2.2, 0.08, 0.13, "B"),
    (40, R_EU, "Низководный мост на Сааремаа (Эстония)", 0.4, 0.8, 0.065, 0.115, 0.8, 1.8, 0.02, 0.07, "B"),
    (41, R_AM, "Горный тоннельный коридор Сьерра-Мадре (Мексика — США)", 15, 20, 2.0, 3.5, 60, 120, 0.5, 1.0, "D"),
    (42, R_AM, "«Сухой» тоннельный коридор Теуантепек (Мексика)", 20, 30, 1.5, 2.5, 8, 15, 0.3, 0.7, "B"),
    (43, R_AM, "Переход через пролив Лонг-Айленд (Нью-Йорк — Коннектикут)", 15, 25, 1.5, 2.2, 50, 55, 0.6, 1.2, "D"),
    (44, R_AM, "Второй тоннель под Гудзоном (Gateway, NJ — Манхэттен)", 14, 16, 1.2, 1.7, 16, 16, 0.8, 1.4, "A"),
    (45, R_AM, "Переход через Калифорнийский залив (Мексика — Баха)", 12, 15, 0.5, 0.8, 15, 25, 0.15, 0.30, "C"),
    (46, R_AM, "Мост через Ла-Плату (Буэнос-Айрес — Колония)", 3, 5, 0.4, 0.6, 1.5, 2.5, 0.1, 0.2, "C"),
    (47, R_AM, "Второй тоннель под гаванью Окленда (Н. Зеландия)", 5, 8, 0.4, 0.6, 8, 18, 0.15, 0.30, "B"),
    (48, R_AM, "Тоннель Агуа-Негра через Анды (Чили — Аргентина)", 1.5, 2.3, 0.20, 0.35, 1.5, 2.3, 0.10, 0.20, "B"),
    (49, R_AM, "Тоннель Сантос — Гуаружа (Бразилия)", 1.2, 2.0, 0.25, 0.45, 1.2, 2.0, 0.12, 0.25, "A"),
    (50, R_AM, "Мост Маракайбо-2 (Венесуэла)", 2.0, 3.0, 0.30, 0.45, 2.0, 3.0, 0.10, 0.20, "C"),
]

assert len(ITEMS) == 50, len(ITEMS)

# Python-side expected sums (for Review sheet + assertions)
exp = {
    "capex_his": sum((r[3] + r[4]) / 2 for r in ITEMS),
    "rev_his": sum((r[5] + r[6]) / 2 for r in ITEMS),
    "capex_real": sum((r[7] + r[8]) / 2 for r in ITEMS),
    "rev_real": sum((r[9] + r[10]) / 2 for r in ITEMS),
    "n_A": sum(1 for r in ITEMS if r[11] == "A"),
    "n_B": sum(1 for r in ITEMS if r[11] == "B"),
    "n_C": sum(1 for r in ITEMS if r[11] == "C"),
    "n_D": sum(1 for r in ITEMS if r[11] == "D"),
}
print("EXPECTED SUMS:", {k: round(v, 2) for k, v in exp.items()})

FMT2 = '#,##0.00'
FMT_PCT = '0%'
GREEN = "008000"   # cross-sheet reference
BLUE = "0000FF"    # manual input

wb = Workbook()

# ---------------------------------------------------------------- Допущения --
ws = wb.active
ws.title = "Допущения"
setup_sheet(ws, title="Допущения модели (синие ячейки — редактируйте)", last_col=5)

headers = ["Класс", "Описание", "Вероятность (база)", "Вероятность (оптимист)"]
for col, h in enumerate(headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, 5)

class_rows = [
    ("A", "Строится или стартует в ближайшие 5 лет", 0.90, 0.95),
    ("B", "Реализуем в 10–15 лет: финансирование + рядовые соглашения", 0.60, 0.80),
    ("C", "Требует крупного геополитического сдвига", 0.18, 0.45),
    ("D", "Практически невозможно в обозримой перспективе", 0.04, 0.12),
]
for i, (k, desc, pb, po) in enumerate(class_rows):
    r = 5 + i
    ws.cell(row=r, column=2, value=k)
    ws.cell(row=r, column=3, value=desc)
    ws.cell(row=r, column=4, value=pb)
    ws.cell(row=r, column=5, value=po)
    style_data_row(ws, r, 2, 5, i)
    for col in (4, 5):
        c = ws.cell(row=r, column=col)
        c.number_format = FMT_PCT
        c.alignment = align_number()
        c.font = Font(name=FONT_NAME, size=11, color=BLUE)  # inputs

ws.cell(row=10, column=2, value="Финансовые допущения")
ws.cell(row=10, column=2).font = font_subheader()
ws.row_dimensions[10].height = 24

fin_headers = ["Параметр", "Значение", "Комментарий"]
for col, h in enumerate(fin_headers, 2):
    ws.cell(row=11, column=col, value=h)
style_header_row(ws, 11, 2, 4)

fin_rows = [
    ("EBITDA-маржа оператора", 0.63, "Типично 60–75% для toll-активов (Transurban 75%, межгород ~70%)"),
    ("Мультипликатор «сделки контроля»", 13.0, "EV/EBITDA сделок 2021–2025: Atlantia ~13–14x, ASPI 8–9x"),
    ("Мультипликатор «биржевая премия»", 28.0, "Transurban ~28x — только для длинных концессий-звёзд"),
    ("Мультипликатор «техно-оптимист»", 18.0, "Премия за прорывные технологии и pipeline новых проектов"),
]
for i, (p, v, note) in enumerate(fin_rows):
    r = 12 + i
    ws.cell(row=r, column=2, value=p)
    ws.cell(row=r, column=3, value=v)
    ws.cell(row=r, column=4, value=note)
    style_data_row(ws, r, 2, 4, i)
    c = ws.cell(row=r, column=3)
    c.number_format = FMT_PCT if i == 0 else '0.0'
    c.alignment = align_number()
    c.font = Font(name=FONT_NAME, size=11, color=BLUE)

auto_fit_columns(ws, min_width=8, max_width=40, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

# ----------------------------------------------------------------- Проекты --
ws = wb.create_sheet("Проекты")
LAST_COL = 22  # B..V
setup_sheet(ws, title="Портфель: 50 проектов — ваши цифры vs реалистичные (все суммы в $ млрд)", last_col=LAST_COL)

proj_headers = [
    "№", "Регион", "Проект",
    "CAPEX ваш, мин", "CAPEX ваш, макс", "CAPEX ваш, сер.",
    "Выручка ваш, мин", "Выручка ваш, макс", "Выручка ваш, сер.",
    "CAPEX реал., мин", "CAPEX реал., макс", "CAPEX реал., сер.",
    "Выручка реал., мин", "Выручка реал., макс", "Выручка реал., сер.",
    "Класс", "P (база)", "P (оптим.)",
    "E(CAPEX), база", "E(выручка), база", "E(выручка), оптим.",
]
for col, h in enumerate(proj_headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, LAST_COL)

DATA_START, DATA_END = 5, 5 + len(ITEMS) - 1  # 5..54
for i, (no, reg, name, cmin, cmax, rmin, rmax, rcmin, rcmax, rrmin, rrmax, kls) in enumerate(ITEMS):
    r = DATA_START + i
    ws.cell(row=r, column=2, value=no)
    ws.cell(row=r, column=3, value=reg)
    ws.cell(row=r, column=4, value=name)
    ws.cell(row=r, column=5, value=cmin)
    ws.cell(row=r, column=6, value=cmax)
    ws.cell(row=r, column=7, value=f"=(E{r}+F{r})/2")
    ws.cell(row=r, column=8, value=rmin)
    ws.cell(row=r, column=9, value=rmax)
    ws.cell(row=r, column=10, value=f"=(H{r}+I{r})/2")
    ws.cell(row=r, column=11, value=rcmin)
    ws.cell(row=r, column=12, value=rcmax)
    ws.cell(row=r, column=13, value=f"=(K{r}+L{r})/2")
    ws.cell(row=r, column=14, value=rrmin)
    ws.cell(row=r, column=15, value=rrmax)
    ws.cell(row=r, column=16, value=f"=(N{r}+O{r})/2")
    ws.cell(row=r, column=17, value=kls)
    ws.cell(row=r, column=18, value=f"=VLOOKUP(Q{r},Допущения!$B$5:$E$8,3,0)")
    ws.cell(row=r, column=19, value=f"=VLOOKUP(Q{r},Допущения!$B$5:$E$8,4,0)")
    ws.cell(row=r, column=20, value=f"=M{r}*R{r}")
    ws.cell(row=r, column=21, value=f"=P{r}*R{r}")
    ws.cell(row=r, column=22, value=f"=P{r}*S{r}")
    style_data_row(ws, r, 2, LAST_COL, i)
    # number formats & alignment
    for col in range(5, 17):
        c = ws.cell(row=r, column=col)
        c.number_format = FMT2
        c.alignment = align_number()
    ws.cell(row=r, column=17).alignment = Alignment(horizontal='center', vertical='center')
    for col in (18, 19):
        c = ws.cell(row=r, column=col)
        c.number_format = FMT_PCT
        c.alignment = align_number()
    for col in (20, 21, 22):
        c = ws.cell(row=r, column=col)
        c.number_format = FMT2
        c.alignment = align_number()
    # VLOOKUP = cross-sheet -> green
    for col in (18, 19):
        c = ws.cell(row=r, column=col)
        c.font = Font(name=FONT_NAME, size=11, color=GREEN)

# conditional formatting on class column
rng = f"Q{DATA_START}:Q{DATA_END}"
ws.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=['"A"'],
    fill=PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid'),
    font=Font(color=ACCENT_POSITIVE)))
ws.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=['"B"'],
    fill=PatternFill(start_color='FEF9E7', end_color='FEF9E7', fill_type='solid'),
    font=Font(color=ACCENT_WARNING)))
ws.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=['"D"'],
    fill=PatternFill(start_color='FDEDEC', end_color='FDEDEC', fill_type='solid'),
    font=Font(color=ACCENT_NEGATIVE)))

# totals row
TOT = DATA_END + 1  # 55
ws.cell(row=TOT, column=2, value="ИТОГО")
ws.cell(row=TOT, column=4, value="50 проектов")
for col in list(range(5, 17)) + [20, 21, 22]:
    letter = get_column_letter(col)
    ws.cell(row=TOT, column=col, value=f"=SUM({letter}{DATA_START}:{letter}{DATA_END})")
style_total_row(ws, TOT, 2, LAST_COL)
for col in list(range(5, 17)) + [20, 21, 22]:
    c = ws.cell(row=TOT, column=col)
    c.number_format = FMT2
    c.alignment = align_number()

ws.freeze_panes = "E5"
auto_fit_columns(ws, min_width=6, max_width=38, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

# ------------------------------------------------------------------ Сводка --
ws = wb.create_sheet("Сводка")
setup_sheet(ws, title="Сводка: регионы и политические классы ($ млрд)", last_col=8)

reg_headers = ["Регион", "Проектов", "CAPEX ваш, сер.", "CAPEX реал., сер.",
               "Выручка ваш, сер.", "Выручка реал., сер.", "E(выручка), база"]
for col, h in enumerate(reg_headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, 8)

regions = [R_AZIA, R_SA, R_EU, R_AM]
for i, reg in enumerate(regions):
    r = 5 + i
    ws.cell(row=r, column=2, value=reg)
    ws.cell(row=r, column=3, value=f"=COUNTIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r})")
    ws.cell(row=r, column=4, value=f"=SUMIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r},Проекты!$G${DATA_START}:$G${DATA_END})")
    ws.cell(row=r, column=5, value=f"=SUMIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r},Проекты!$M${DATA_START}:$M${DATA_END})")
    ws.cell(row=r, column=6, value=f"=SUMIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r},Проекты!$J${DATA_START}:$J${DATA_END})")
    ws.cell(row=r, column=7, value=f"=SUMIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r},Проекты!$P${DATA_START}:$P${DATA_END})")
    ws.cell(row=r, column=8, value=f"=SUMIF(Проекты!$C${DATA_START}:$C${DATA_END},B{r},Проекты!$U${DATA_START}:$U${DATA_END})")
    style_data_row(ws, r, 2, 8, i)
    for col in range(3, 9):
        c = ws.cell(row=r, column=col)
        c.number_format = '0' if col == 3 else FMT2
        c.alignment = align_number()

REG_TOT = 9
ws.cell(row=REG_TOT, column=2, value="ИТОГО")
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=REG_TOT, column=col, value=f"=SUM({letter}5:{letter}8)")
style_total_row(ws, REG_TOT, 2, 8)
for col in range(3, 9):
    c = ws.cell(row=REG_TOT, column=col)
    c.number_format = '0' if col == 3 else FMT2
    c.alignment = align_number()

# class block
ws.cell(row=12, column=2, value="По классам политической осуществимости")
ws.cell(row=12, column=2).font = font_subheader()
ws.row_dimensions[12].height = 24

cls_headers = ["Класс", "Проектов", "CAPEX ваш, сер.", "CAPEX реал., сер.",
               "Выручка ваш, сер.", "Выручка реал., сер.", "E(выручка), база"]
for col, h in enumerate(cls_headers, 2):
    ws.cell(row=13, column=col, value=h)
style_header_row(ws, 13, 2, 8)

for i, k in enumerate(["A", "B", "C", "D"]):
    r = 14 + i
    ws.cell(row=r, column=2, value=f'"{k}"' if False else k)
    ws.cell(row=r, column=3, value=f"=COUNTIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r})")
    ws.cell(row=r, column=4, value=f"=SUMIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r},Проекты!$G${DATA_START}:$G${DATA_END})")
    ws.cell(row=r, column=5, value=f"=SUMIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r},Проекты!$M${DATA_START}:$M${DATA_END})")
    ws.cell(row=r, column=6, value=f"=SUMIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r},Проекты!$J${DATA_START}:$J${DATA_END})")
    ws.cell(row=r, column=7, value=f"=SUMIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r},Проекты!$P${DATA_START}:$P${DATA_END})")
    ws.cell(row=r, column=8, value=f"=SUMIF(Проекты!$Q${DATA_START}:$Q${DATA_END},B{r},Проекты!$U${DATA_START}:$U${DATA_END})")
    style_data_row(ws, r, 2, 8, i)
    for col in range(3, 9):
        c = ws.cell(row=r, column=col)
        c.number_format = '0' if col == 3 else FMT2
        c.alignment = align_number()

CLS_TOT = 18
ws.cell(row=CLS_TOT, column=2, value="ИТОГО")
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=CLS_TOT, column=col, value=f"=SUM({letter}14:{letter}17)")
style_total_row(ws, CLS_TOT, 2, 8)
for col in range(3, 9):
    c = ws.cell(row=CLS_TOT, column=col)
    c.number_format = '0' if col == 3 else FMT2
    c.alignment = align_number()

# key insight row
ws.cell(row=20, column=2, value="Доля выручки (ваши цифры) в заблокированных классах C+D")
ws.cell(row=20, column=2).font = font_body()
dcell = ws.cell(row=20, column=4, value=f"=IF(F{CLS_TOT}=0,0,(F16+F17)/F{CLS_TOT})")
dcell.number_format = '0.0%'
dcell.font = Font(name=FONT_NAME, size=11, bold=HEADER_BOLD, color=ACCENT_NEGATIVE)
dcell.alignment = align_number()

note = ws.cell(row=22, column=2, value="Классы: A — строится/стартует в 5 лет; B — реализуем в 10–15 лет; C — нужен геополитический сдвиг; D — практически невозможно.")
note.font = font_caption()

auto_fit_columns(ws, min_width=8, max_width=34, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

# chart: E(revenue) by class
chart = create_bar_chart()
data = Reference(ws, min_col=8, min_row=13, max_row=17)
cats = Reference(ws, min_col=2, min_row=14, max_row=17)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
setup_chart_titles(chart, title="Ожидаемая выручка по классам (база, $ млрд/год)")
apply_chart_colors(chart)
ws.add_chart(chart, "J13")

# --------------------------------------------------------- Оценка компании --
ws = wb.create_sheet("Оценка компании")
setup_sheet(ws, title="Сколько стоит корпорация: EV = Выручка × EBITDA-маржа × мультипликатор", last_col=8)

val_headers = ["Сценарий", "Выручка, $ млрд/год", "Маржа", "EBITDA, $ млрд",
               "Мультипликатор", "EV, $ млрд", "Комментарий"]
for col, h in enumerate(val_headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, 8)

scenarios = [
    ("«Как в вашем документе» (все 50, ваши выручки, биржевой мультипликатор)",
     f"='Проекты'!J{TOT}", "=Допущения!$C$12", "=Допущения!$C$14",
     "Требует построить ВСЕ 50 включая Тайвань и Корею—Японию + премию Transurban — вот откуда «$1 трлн»"),
    ("«Все 50 построены» — реалистичный спрос",
     f"='Проекты'!P{TOT}", "=Допущения!$C$12", "=Допущения!$C$13",
     "Потолок без учёта политики: каждый проект вышел на реалистичный трафик"),
    ("«База» — взвешено вероятностями реализации",
     f"='Проекты'!U{TOT}", "=Допущения!$C$12", "=Допущения!$C$13",
     "Только ожидаемая доля портфеля будет построена и выйдет на трафик"),
    ("«Оптимист» — вероятности + техно-премия",
     f"='Проекты'!V{TOT}", "=Допущения!$C$12", "=Допущения!$C$15",
     "Прорывные технологии снижают CAPEX и включают часть класса C"),
]
for i, (name, rev_f, m_f, mult_f, note_txt) in enumerate(scenarios):
    r = 5 + i
    ws.cell(row=r, column=2, value=name)
    ws.cell(row=r, column=3, value=rev_f)
    ws.cell(row=r, column=4, value=m_f)
    ws.cell(row=r, column=5, value=f"=C{r}*D{r}")
    ws.cell(row=r, column=6, value=mult_f)
    ws.cell(row=r, column=7, value=f"=E{r}*F{r}")
    ws.cell(row=r, column=8, value=note_txt)
    style_data_row(ws, r, 2, 8, i)
    ws.cell(row=r, column=3).font = Font(name=FONT_NAME, size=11, color=GREEN)
    for col, fmt in ((3, '#,##0'), (4, FMT_PCT), (5, '#,##0'), (6, '0.0'), (7, '#,##0')):
        c = ws.cell(row=r, column=col)
        c.number_format = fmt
        c.alignment = align_number()
        if col in (4, 6):
            c.font = Font(name=FONT_NAME, size=11, color=GREEN)

# comparison block
ws.cell(row=11, column=2, value="Сравнение с реальными компаниями (капитализация, конец 2025)")
ws.cell(row=11, column=2).font = font_subheader()
ws.row_dimensions[11].height = 24

cmp_headers = ["Компания", "Капитализация, $ млрд", "Примечание"]
for col, h in enumerate(cmp_headers, 2):
    ws.cell(row=12, column=col, value=h)
style_header_row(ws, 12, 2, 4)

comps = [
    ("Nvidia", 4400, "крупнейшая в мире"),
    ("Apple", 4100, ""),
    ("Saudi Aramco", 1700, "крупнейшая вне США"),
    ("Tesla", 1400, ""),
    ("Shell", 220, "энергетика/инфра-масштаб"),
    ("Transurban", 30, "крупнейший «чистый» toll-оператор мира"),
    ("Getlink (Евротоннель)", 12, "реальный владелец Евротоннеля"),
    ("ВАША КОРПОРАЦИЯ — сценарий «База»", "=G7", "оживлено формулой"),
    ("ВАША КОРПОРАЦИЯ — сценарий «Оптимист»", "=G8", "оживлено формулой"),
]
for i, (n, v, note_txt) in enumerate(comps):
    r = 13 + i
    ws.cell(row=r, column=2, value=n)
    ws.cell(row=r, column=3, value=v)
    ws.cell(row=r, column=4, value=note_txt)
    style_data_row(ws, r, 2, 4, i)
    c = ws.cell(row=r, column=3)
    c.number_format = FMT2
    c.alignment = align_number()
    if isinstance(v, str):
        c.font = Font(name=FONT_NAME, size=11, color=GREEN)

ws.cell(row=24, column=2, value="Мемо: ваша выручка $63 млрд = ~40% всего мирового рынка платных дорог (Китай $94 млрд + США $23–25 млрд; весь мир ~$150–200 млрд/год).")
ws.cell(row=24, column=2).font = font_caption()

auto_fit_columns(ws, min_width=8, max_width=44, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

# chart: EV by scenario
chart2 = create_bar_chart()
data2 = Reference(ws, min_col=7, min_row=4, max_row=8)
cats2 = Reference(ws, min_col=2, min_row=5, max_row=8)
chart2.add_data(data2, titles_from_data=True)
chart2.set_categories(cats2)
setup_chart_titles(chart2, title="EV корпорации по сценариям, $ млрд")
apply_chart_colors(chart2)
ws.add_chart(chart2, "B26")

# ----------------------------------------------------------------- Беларусь --
ws = wb.create_sheet("Беларусь")
setup_sheet(ws, title="Пакет «Подарок Родине» ($35–40 млрд): документ vs реальность", last_col=5)

blr_headers = ["Параметр", "В вашем документе", "Реалистично", "Комментарий"]
for col, h in enumerate(blr_headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, 5)

blr_rows = [
    ("CAPEX пакета", "$35–40 млрд", "$15–30 млрд",
     "Канал 70 км с 6–8 шлюзами $3–6 млрд; 8–10 гидроузлов $4–8 млрд; ДБК $2–4 млрд; герметичный обход Полесья/ЧЗО $5–10 млрд; шлюзы на Даугаве $2–4 млрд"),
    ("Прирост ВВП", "+35–55% (+$25–40 млрд/год)", "+3–7% (+$2,5–5,5 млрд/год)",
     "ВВП Беларуси 2024 = $78,6 млрд; весь экспорт транспортных услуг = $4,5 млрд/год (2024); транспорт = 6–7% ВВП"),
    ("Горизонт эффекта", "не указан", "15–25 лет после снятия вето",
     "Стройка 10–15 лет + накопление грузовой базы"),
    ("Рабочие места (прямые)", "120 000–180 000", "20–40 тыс. на пике стройки; 10–20 тыс. постоянных",
     "Операторы шлюзов, порты, диспетчеризация, верфи"),
    ("Суверенный фонд", "«по норвежской модели»", "$15–30 млрд к 2060-м",
     "Норвегия: $2+ трлн на потоках $50–100 млрд/год × 30 лет; белорусские активы дадут EBITDA $1–2 млрд/год"),
    ("Единая колея 1435 мм / ВСМ", "входит в пакет", "$8–15 млрд (Брест — Минск — Орша/Витебск)",
     "Прецедент: Rail Baltica (€15+ млрд). При нормализации — включение в TEN-T"),
    ("Политические вето", "не учтены", "4 вето: ЕС (санкции), Латвия, Польша, Украина",
     "ГЭС Даугавы без шлюзов; Буг — Natura 2000 (польский участок E40 €11,9 млрд отклонён); транзит Китай—ЕС уже −77%"),
    ("Инженерная база", "«Водный крест», герметичный канал", "корректна: прецедент — Березинская система 1797–1805 (14 шлюзов)",
     "Шлюзы в ГЭС Латвии и обход заповедников — правильные ответы на реальные возражения"),
]
for i, row in enumerate(blr_rows):
    r = 5 + i
    for col, v in enumerate(row, 2):
        ws.cell(row=r, column=col, value=v)
    style_data_row(ws, r, 2, 5, i)

auto_fit_columns(ws, min_width=10, max_width=42, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

# ------------------------------------------------------------------- Review --
ws = wb.create_sheet("Review")
ws.sheet_properties.tabColor = "FFC000"
setup_sheet(ws, title="Review: кросс-проверки модели", last_col=5)

rv_headers = ["Проверка", "Ожидание", "Факт", "Статус"]
for col, h in enumerate(rv_headers, 2):
    ws.cell(row=4, column=col, value=h)
style_header_row(ws, 4, 2, 5)

checks = [
    ("Число проектов", 50, f"=COUNT(Проекты!B{DATA_START}:B{DATA_END})"),
    ("Σ CAPEX ваш (середины), $ млрд", round(exp["capex_his"], 1), f"=ROUND(Проекты!G{TOT},1)"),
    ("Σ Выручка ваш (середины), $ млрд/год", round(exp["rev_his"], 1), f"=ROUND(Проекты!J{TOT},1)"),
    ("Σ CAPEX реал. (середины), $ млрд", round(exp["capex_real"], 1), f"=ROUND(Проекты!M{TOT},1)"),
    ("Σ Выручка реал. (середины), $ млрд/год", round(exp["rev_real"], 1), f"=ROUND(Проекты!P{TOT},1)"),
    ("Проектов класса A", exp["n_A"], f"=COUNTIF(Проекты!Q{DATA_START}:Q{DATA_END},\"A\")"),
    ("Проектов класса B", exp["n_B"], f"=COUNTIF(Проекты!Q{DATA_START}:Q{DATA_END},\"B\")"),
    ("Проектов класса C", exp["n_C"], f"=COUNTIF(Проекты!Q{DATA_START}:Q{DATA_END},\"C\")"),
    ("Проектов класса D", exp["n_D"], f"=COUNTIF(Проекты!Q{DATA_START}:Q{DATA_END},\"D\")"),
    ("Σ E(выручка) база = Σ по классам", f"=ROUND(Проекты!U{TOT},2)", "=ROUND(Сводка!H18,2)"),
]
for i, (name, expected, actual) in enumerate(checks):
    r = 5 + i
    ws.cell(row=r, column=2, value=name)
    ws.cell(row=r, column=3, value=expected)
    ws.cell(row=r, column=4, value=actual)
    ws.cell(row=r, column=5, value=f"=IF(C{r}=D{r},\"✓ PASS\",\"✗ FAIL\")")
    style_data_row(ws, r, 2, 5, i)
    for col in (3, 4):
        c = ws.cell(row=r, column=col)
        c.number_format = FMT2 if not isinstance(expected, str) else FMT2
        c.alignment = align_number()
        if isinstance(expected, str) or str(actual).startswith("='"):
            c.font = Font(name=FONT_NAME, size=11, color=GREEN)

auto_fit_columns(ws, min_width=10, max_width=40, header_row=4, data_start_row=5)
auto_fit_row_heights(ws, header_row=4, data_start_row=5)

for sheet in wb.worksheets:
    setup_print(sheet, fit_height=0 if sheet.title == "Проекты" else 1)

wb.properties.creator = "Z.ai"
wb.save(OUT)
print("SAVED:", OUT)
