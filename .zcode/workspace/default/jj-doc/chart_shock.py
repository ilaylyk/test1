# Horizontal bar chart: scenario price multipliers vs current (Oct 2026) levels
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = [
    ("Обогащение урана (SWU)", 4.0),
    ("Калийные удобрения", 3.0),
    ("Газ TTF (ЕС)", 2.5),
    ("Палладий (пик шока)", 2.25),
    ("Пшеница", 2.15),
    ("Подсолнечное масло", 1.95),
    ("Титан (прокат)", 1.9),
    ("Нефть Brent", 1.65),
    ("Уран (спот)", 1.75),
    ("Уголь", 1.75),
    ("Алюминий", 1.6),
    ("Никель", 1.45),
]
data = sorted(data, key=lambda x: x[1])  # ascending → largest ends up on top

RED = "#9E2B25"      # x >= 2.5 — экстремальный шок
MID = "#B3763B"      # 1.8-2.5
MUTED = "#8A8F98"    # < 1.8
colors = [RED if v >= 2.5 else (MID if v >= 1.8 else MUTED) for _, v in data]

names = [n for n, _ in data]
vals = [v for _, v in data]

fig, ax = plt.subplots(figsize=(10.2, 6.4), dpi=200)
bars = ax.barh(names, vals, color=colors, height=0.62, zorder=3)

for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f"×{v:.2f}".rstrip("0").rstrip("."), va="center", ha="left",
            fontsize=9.5, color="#333333", zorder=4)

ax.axvline(1.0, color="#555555", linewidth=1.0, linestyle="--", zorder=2)
ax.text(1.02, len(names) - 0.35, "текущий уровень = 1", fontsize=9, color="#555555")

ax.set_xlim(0, 4.6)
ax.set_xlabel("Кратность к уровню октября 2026 года (сценарий полной эскалации)", fontsize=9.5, color="#555555")
ax.set_title("Сценарные мультипликаторы цен: вывод экспортных отраслей РФ из строя",
             fontsize=12.5, color="#1E2A3A", pad=14, fontweight="bold")
ax.tick_params(axis="y", labelsize=9.5, colors="#333333")
ax.tick_params(axis="x", labelsize=9, colors="#555555")
ax.grid(axis="x", color="#DDDDDD", linewidth=0.7, zorder=0)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")

from matplotlib.patches import Patch
legend = [
    Patch(facecolor=RED, label="×2,5 и выше — дефицит мощностей неустраним быстро"),
    Patch(facecolor=MID, label="×1,8–2,5 — сильный шок с замещением"),
    Patch(facecolor=MUTED, label="ниже ×1,8 — замещение работает"),
]
ax.legend(handles=legend, loc="lower right", fontsize=9, frameon=False)

fig.tight_layout()
fig.savefig("chart_shock.png", dpi=200, facecolor="white")
print("saved chart_shock.png")
