# Horizontal bar chart: Russia's share of key global markets
# Palette matched to generate_russia.js (bronze accent).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = [
    ("Янтарь-сырец (добыча)", 65),
    ("Обогащение урана (мощности)", 44),
    ("Палладий (добыча)", 40),
    ("АЭС: строящиеся блоки (Росатом)", 37),
    ("Калийные удобрения, РФ+РБ (торговля)", 37),
    ("Алмазы (добыча, объём)", 30),
    ("Подсолнечное масло (экспорт)", 30),
    ("Титан для авиации (рынок)", 25),
    ("Пшеница (экспорт)", 24),
    ("Удобрения в целом (торговля)", 20),
    ("Никель класса 1 (выпуск)", 14),
    ("Уголь (экспорт)", 13),
    ("Нефть (экспорт)", 11),
    ("Платина (добыча)", 10),
    ("СПГ (экспорт)", 8),
    ("Вооружения (экспорт)", 8),
]
data = data[::-1]  # largest on top after barh

ACCENT = "#B3763B"       # >= 40% — фактическая монополия / доминирование
MID = "#7A6A52"          # 20-40%
MUTED = "#A9B2BC"        # < 20%
colors = [ACCENT if v >= 40 else (MID if v >= 20 else MUTED) for _, v in data]

names = [n for n, _ in data]
vals = [v for _, v in data]

fig, ax = plt.subplots(figsize=(10.2, 6.6), dpi=200)
bars = ax.barh(names, vals, color=colors, height=0.62, zorder=3)

for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
            f"~{v}%", va="center", ha="left", fontsize=9.5, color="#333333", zorder=4)

ax.set_xlim(0, 74)
ax.set_xlabel("Доля, % (базы расчёта различаются: добыча, экспорт или мощности)", fontsize=9.5, color="#555555")
ax.set_title("Доля России на ключевых мировых рынках (2024–2026, оценки)",
             fontsize=13, color="#1E2A3A", pad=14, fontweight="bold")
ax.tick_params(axis="y", labelsize=9.5, colors="#333333")
ax.tick_params(axis="x", labelsize=9, colors="#555555")
ax.grid(axis="x", color="#DDDDDD", linewidth=0.7, zorder=0)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")

from matplotlib.patches import Patch
legend = [
    Patch(facecolor=ACCENT, label="40% и выше — фактическая монополия"),
    Patch(facecolor=MID, label="20–40% — доминирование / лидерство"),
    Patch(facecolor=MUTED, label="ниже 20% — значимая доля"),
]
ax.legend(handles=legend, loc="lower right", fontsize=9, frameon=False)

fig.tight_layout()
fig.savefig("chart_russia.png", dpi=200, facecolor="white")
print("saved chart_russia.png")
