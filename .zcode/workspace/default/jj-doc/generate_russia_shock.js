// Шок-сценарий: вывод экспортных отраслей России из строя — сценарно-аналитический отчёт (Russian)
// Recipe: R1 (Pure Paragraph Left), graphite/crimson palette, per docx skill design system.
// Builder reused from generate_russia.js pipeline (validated 16/16 pass on 14.10.2026).
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, SectionType, TableLayoutType,
  TableOfContents, PageBreak, ExternalHyperlink, LevelFormat, ImageRun,
} = require("docx");
const fs = require("fs");
const path = require("path");

const P = {
  bg: "26262B",
  accent: "9E2B25",
  cover: { titleColor: "FFFFFF", subtitleColor: "C8C8CE", metaColor: "9A9AA2", footerColor: "6E6E76" },
  table: { headerBg: "9E2B25", headerText: "FFFFFF", innerLine: "D9C4C2", surface: "F5ECEB" },
  headingColor: "26262B",
  body: "000000",
  secondary: "505050",
};

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([...",;:", ..."-_—–·/", ..." \t"]);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) breakAt = charsPerLine;
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}

function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charWidth = (pt) => pt * 11.5;
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / charWidth(pt));
  let titlePt = preferredPt;
  let lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

function calcCoverSpacing(params) {
  const {
    titleLineCount = 1, titlePt = 36, hasSubtitle = false,
    hasEnglishLabel = false, metaLineCount = 0,
    fixedHeight = 800, pageHeight = 16838, marginTop = 0, marginBottom = 0,
  } = params;
  const SAFETY = 1200;
  const usableHeight = pageHeight - marginTop - marginBottom - SAFETY;
  const titleHeight = titleLineCount * (titlePt * 23 + 200);
  const subtitleHeight = hasSubtitle ? (12 * 23 + 600) : 0;
  const englishLabelHeight = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaHeight = metaLineCount * (10 * 23 + 100);
  const implicitParaHeight = 3 * 300;
  const contentHeight = titleHeight + subtitleHeight + englishLabelHeight + metaHeight + fixedHeight + implicitParaHeight;
  const remainingSpace = usableHeight - contentHeight;
  const safeRemaining = Math.max(remainingSpace, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(safeRemaining * 0.45);
  const rawBottom = Math.floor(safeRemaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  const midSpacing = Math.max(safeRemaining - topSpacing - bottomSpacing, 0);
  return { topSpacing, midSpacing, bottomSpacing };
}

function buildCoverR1(config) {
  const C = config.palette;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length,
    fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8, color: C.accent, space: 12 };
  const children = [];

  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));

  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 8 } },
      children: [new TextRun({
        text: config.englishLabel.split("").join("  "),
        size: 18, color: C.accent, font: { ascii: "Arial", hAnsi: "Arial" }, characterSpacing: 40,
      })],
    }));
  }

  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({
        text: titleLines[i], size: titleSize, bold: true,
        color: C.cover.titleColor, font: { ascii: "Arial", hAnsi: "Arial" },
      })],
    }));
  }

  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 800 },
      children: [new TextRun({
        text: config.subtitle, size: 24, color: C.cover.subtitleColor,
        font: { ascii: "Arial", hAnsi: "Arial" },
      })],
    }));
  }

  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200, right: padR }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({
        text: line, size: 22, color: C.cover.metaColor, font: { ascii: "Arial", hAnsi: "Arial" },
      })],
    }));
  }

  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));

  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16, color: C.cover.footerColor, font: { ascii: "Arial", hAnsi: "Arial" } }),
      new TextRun({ text: "                                        ", font: { ascii: "Arial", hAnsi: "Arial" } }),
      new TextRun({ text: config.footerRight || "", size: 16, color: C.cover.footerColor, font: { ascii: "Arial", hAnsi: "Arial" } }),
    ],
  }));

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: C.bg }, borders: noBorders,
        children,
      })],
    })],
  })];
}

const FONT_BODY = { ascii: "Times New Roman", hAnsi: "Times New Roman" };
const FONT_HEAD = { ascii: "Arial", hAnsi: "Arial" };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    keepNext: true,
    spacing: { before: 400, after: 180, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: P.headingColor, font: FONT_HEAD })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    keepNext: true,
    spacing: { before: 280, after: 140, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: P.headingColor, font: FONT_HEAD })],
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 709 },
    spacing: { line: 312, after: 80 },
    children: [new TextRun({ text, size: 24, color: P.body, font: FONT_BODY })],
    ...opts,
  });
}

function pRuns(runs, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 709 },
    spacing: { line: 312, after: 80 },
    children: runs,
    ...opts,
  });
}

function r(text, extra = {}) {
  return new TextRun({ text, size: 24, color: P.body, font: FONT_BODY, ...extra });
}

function quote(text, attribution) {
  const runs = [new TextRun({ text, italics: true, size: 23, color: "3A3A3A", font: FONT_BODY })];
  if (attribution) {
    runs.push(new TextRun({ text: "  " + attribution, size: 21, color: P.secondary, font: FONT_BODY }));
  }
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 500, right: 500 },
    spacing: { line: 312, before: 100, after: 140 },
    border: { left: { style: BorderStyle.SINGLE, size: 10, color: P.accent, space: 12 } },
    children: runs,
  });
}

function caption(text) {
  return new Paragraph({
    keepNext: true,
    spacing: { before: 200, after: 80, line: 312 },
    children: [new TextRun({ text, bold: true, size: 21, color: P.headingColor, font: FONT_HEAD })],
  });
}

function cell(text, opts = {}) {
  const { header = false, width = 25, fill = null, small = false } = opts;
  return new TableCell({
    width: { size: width, type: WidthType.PERCENTAGE },
    margins: { top: 70, bottom: 70, left: 120, right: 120 },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
    children: [new Paragraph({
      spacing: { line: 276 },
      children: [new TextRun({
        text, size: small ? 17 : (header ? 21 : 20), bold: header,
        color: header ? P.table.headerText : P.body,
        font: header ? FONT_HEAD : FONT_BODY,
      })],
    })],
  });
}

function mkTable(headers, rows, widths, opts = {}) {
  const { small = false } = opts;
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: P.accent },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: P.accent },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({
        tableHeader: true, cantSplit: true,
        children: headers.map((t, i) => cell(t, { header: true, width: widths[i], fill: P.table.headerBg, small })),
      }),
      ...rows.map((row, ri) => new TableRow({
        cantSplit: true,
        children: row.map((t, i) => cell(t, { width: widths[i], fill: ri % 2 === 0 ? P.table.surface : "FFFFFF", small })),
      })),
    ],
  });
}

function srcItem(label, url) {
  const runs = [new TextRun({ text: label + (url ? " — " : ""), size: 20, color: P.body, font: FONT_BODY })];
  if (url) {
    runs.push(new ExternalHyperlink({
      link: url,
      children: [new TextRun({ text: url, style: "Hyperlink", size: 20, font: FONT_BODY })],
    }));
  }
  return new Paragraph({
    numbering: { reference: "src-list", level: 0 },
    spacing: { line: 276, after: 40 },
    children: runs,
  });
}

// ─────────────────────────────────────────────────────────────
// Body content
// ─────────────────────────────────────────────────────────────
const body = [];

// ============ 1. Резюме ============
body.push(h1("1. Резюме"));
body.push(p("Вопрос отчёта: что произойдёт с мировыми ценами, если экспортные отрасли России из первого отчёта — обогащение урана, палладий, калий, пшеница, титан, нефть, газ — будут в теории выведены из строя, и какие публичные компании исторически и структурно выигрывают от таких шоков предложения."));
body.push(pRuns([
  r("Мультипликаторы известны — 2022 год их уже показал. ", { bold: true }),
  r("Частичный шок (санкции без физического разрушения) дал: пшеница ×2 (рекорд 12,94 доллара за бушель), калий ×4 (около 1 100 долларов за тонну в Бразилии), палладий плюс 50% (исторический максимум 3 440 долларов за унцию), газ TTF ×5 (339 евро за МВт·ч). Полное физическое устранение поставщика даёт более сильные и долгие шоки: обогащение (SWU) ×3–5, калий ×2,5–3,5 от текущих уровней, Brent 150–200 долларов, TTF 170–250 евро."),
]));
body.push(pRuns([
  r("Часть сценария уже в ценах октября 2026 года. ", { bold: true }),
  r("Brent стоит около 107–125 долларов (максимум с 2022 года), газ TTF — около 85 евро (высший уровень с декабря 2022-го), пшеница плюс 40% за 2026 год, палладий плюс 81% за 2025-й, уран около 90 долларов за фунт, SWU около 200 долларов против 50 до 2022-го. Рынок уже торгуемо покупает обострение — лёгких денег «до ударов» на бирже нет."),
]));
body.push(pRuns([
  r("Урок 2022 года: спайки возвращаются, структуры остаются. ", { bold: true }),
  r("Палладий с пика 3 440 долларов упал до 813 (минус 76%), калий минус 75%, пшеница минус 61%, TTF минус 90%. А структурные бенефициары удержали и приумножили: SWU ×4 и держится, Centrus вырос с 10 долларов до двухсот с лишним, Rheinmetall — примерно в двадцать раз с 2022 года. Выигрывает тот, кто покупает структурный сдвиг, а не панику."),
]));
body.push(pRuns([
  r("«Заработать перед ударами» легально нельзя — и не нужно. ", { bold: true }),
  r("Точных ударов не предсказывает никто; сделки на основе внутренней информации о готовящихся атаках — уголовный инсайд в США и ЕС. Легальная альтернатива — позиционирование на вероятностях: хедж через опционы «вне денег» на бенефициарах и структурные позиции на долгие тренды (обогащение, переоснащение Европы, СПГ)."),
]));
body.push(quote("Этот отчёт — образовательный стресс-тест рынков, а не индивидуальная инвестиционная рекомендация. Все упомянутые бумаги — иллюстрация отраслевой экспозиции, а не совет покупать.", "дисклеймер"));

// ============ 2. Рамка ============
body.push(h1("2. Рамка, этика и ограничения"));
body.push(pRuns([
  r("Теоретичность. ", { bold: true }),
  r("Сценарий «все отрасли уничтожены» — предельный стресс-тест. География не позволяет уничтожить обогащение урана (Ангарск — тысячи километров от фронта) или калийные комбинаты (Урал, Пермь). Реалистичный сценарий — удары по НПЗ, портам, терминалам и железнодорожной погрузке (это уже происходит с 2024 года) и их эскалация; экстремальный — полное прекращение экспорта (блокада, тотальный санкционный режим покупателей)."),
]));
body.push(pRuns([
  r("Инсайд и этика. ", { bold: true }),
  r("Фраза «купить перед ударами» легально реализуема только как ставка на вероятность, доступную всем участникам рынка. Торговля на основе непубличной информации о готовящихся конкретных атаках — инсайд с уголовной ответственностью в США, ЕС и Великобритании. Отчёт не даёт и не может давать тайминга — только карту бенефициаров и ценовую механику."),
]));
body.push(pRuns([
  r("Не инвестсовет. ", { bold: true }),
  r("Рынки 2026 года перегреты по обороне (профит-тейкинг с апреля 2026-го), большинство опционов сгорает, плечо убивает. Решения — на свой риск, в идеале с лицензированным консультантом."),
]));

// ============ 3. Реалистичность ============
body.push(h1("3. Реалистичность: что Украина может, а что нет"));
body.push(caption("Таблица 1. Уязвимость отраслей к физическому воздействию"));
body.push(mkTable(
  ["Цель", "Реализуемо ударами?", "Факт 2024–2026"],
  [
    ["НПЗ и нефтепереработка", "да — уязвимы, восстановление занимает месяцы", "массовые атаки дронов 2025 заставляли РФ вводить запреты на экспорт бензина"],
    ["Экспортные порты и терминалы", "да (Новороссийск, Приморск)", "атаки на Новороссийск в 2025; страховые премии фрахта уже закладывают риск"],
    ["СПГ-терминалы", "частично", "устойчивых выводов нет"],
    ["Обогащение урана (Сибирь)", "практически нет", "глубинный тыл"],
    ["Калийные комбинаты (Урал)", "практически нет", "глубинный тыл"],
    ["Зерновой экспорт (порты, ЖД)", "да", "морской коридор чувствителен к ударам"],
    ["Алмазы (Якутия)", "нет", "—"],
  ],
  [28, 30, 42]
));
body.push(p("Вывод: полный вариант сценария — гипотетический; реалистичный — «нефть и нефтепродукты плюс логистика», и он уже частично отработан рынком."));

// ============ 4. Что уже в ценах ============
body.push(h1("4. Что уже в ценах (октябрь 2026)"));
body.push(caption("Таблица 2. Дошикные уровни, пики шока и текущие цены"));
body.push(mkTable(
  ["Рынок", "Дошикной уровень", "Пик шока 2022–24", "Октябрь 2026", "Комментарий"],
  [
    ["Brent", "~$60–70 (2021, 2025)", "$128 (03.2022)", "~$107–125", "+60% за март 2026 — рекорд месячного роста"],
    ["Газ TTF", "€15–20 (2020)", "€339 (08.2022)", "~€85 (фронт)", "максимум с декабря 2022; ×4 от дошикного"],
    ["Пшеница CBOT", "~$6 (2021)", "$12,94 (03.2022)", "~$6,7–7,8", "+40% за 2026 при слабом урожае"],
    ["Уран спот", "~$30 (2020)", "$107 (02.2024)", "~$90", "долгосрочная цена $97 — исторический максимум"],
    ["Обогащение SWU", "~$50 (2021)", "—", "~$200", "×4 на частичном сценарии без физики"],
    ["Палладий", "~$1 900 (2021)", "$3 440 (03.2022)", "~$1 650 (кон. 2025)", "+81% за 2025; цель BofA $2 200"],
    ["Калий (Бразилия)", "~$250 (2021)", "~$1 100 (04.2022)", "~$370–505", "прогноз +12% на 2026 (Всемирный банк)"],
  ],
  [15, 18, 18, 17, 32],
  { small: true }
));
body.push(p("Смысл таблицы: рынок уже «предоплатил» умеренную версию сценария. Маржинальный апсайд остаётся только на эскалацию сверх текущих ожиданий — и он меньше, чем был в 2021 году при входе с нуля."));
body.push(h2("4.1. Наглядное сопоставление"));
body.push(caption("Диаграмма 1. Сценарные мультипликаторы цен (к уровню октября 2026)"));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  keepNext: true,
  spacing: { after: 60 },
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(__dirname, "chart_shock.png")),
    transformation: { width: 580, height: 364 },
  })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 160 },
  children: [new TextRun({
    text: "Оценки для сценария полной эскалации на основе аналогов 2022 года и структурных дефицитов. Красный — дефицит мощностей неустраним быстро; бронзовый — сильный шок с замещением; серый — замещение работает.",
    italics: true, size: 18, color: "888888", font: FONT_BODY,
  })],
}));

// ============ 5. Поотраслевая механика ============
body.push(h1("5. Поотраслевая механика шока и бенефициары"));

body.push(h2("5.1. Обогащение урана — самый чистый сценарий"));
body.push(p("База: Россия — около 44% мировых мощностей обогащения; США в 2025 году снова импортировали 24,5% обогащённого урана из РФ по исключениям. Заменить мощности нельзя до 2028 года и позже даже политической волей: центрифужные заводы строятся более десяти лет (Urenco и Orano расширяются, Centrus строит American Centrifuge — малыми темпами)."));
body.push(pRuns([
  r("Сценарная оценка: ", { bold: true }),
  r("SWU ×3–5 от текущих (400–600 долларов за SWU), спот-уран 135–180 долларов за фунт. "),
  r("Бенефициары: ", { bold: true }),
  r("Centrus Energy (LEU) — единственный листингованный западный обогатитель, контракт HALEU на 900 млн долларов (2 кв. 2026), рост с ~10 долларов в 2020-м до максимума выше 200 в 2025–26; Cameco (CCJ) — майнер плюс 49% Westinghouse; ETF URA и URNM; майнеры Kazatomprom (GDR), NexGen (NXE), Denison (DNN), Paladin (PDN.AX), Uranium Energy (UEC); генерация — Constellation (CEG), Vistra (VST); реакторные технологии — BWXT, GE Vernova (GEV)."),
]));

body.push(h2("5.2. Палладий: сильнейший шок, главная ловушка"));
body.push(p("База: около 40% мировой добычи. Кейс 2022 года: только страх дефицита (без физического разрушения) поднял цену на 50% к максимуму 3 440 долларов. Физическое устранение 40% предложения — 4 000–5 000 долларов и выше на пике. Но именно палладий — главная ловушка замещения: в 2022–2024 годах автопром пересадил катализаторы на платину, и палладий рухнул на 76%, до 813 долларов, несмотря на войну."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("пик ×2–2,5 от текущих (3 300–4 100 долларов), затем минус 50% за 12–18 месяцев по мере замещения платиной. "),
  r("Бенефициары: ", { bold: true }),
  r("Sibanye-Stillwater (SBSW) — единственный палладиевый майнер Запада (Stillwater, США); Impala Platinum; Anglo American (AAL.L); платина как замещающий металл (ETF типа PLTM)."),
]));

body.push(h2("5.3. Калийные удобрения: образцовый кейс 2022 года"));
body.push(p("База: РФ и РБ — 35–40% мировой торговли. Санкции на «Беларуськалий» подняли бразильский калий с 250 до примерно 1 100 долларов за тонну (×4,4), затем последовал обвал на 75%, до 278 долларов к октябрю 2024-го."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("×2,5–3,5 от текущих (370–505 долларов → 900–1 300), выше при панических закупках Китая. "),
  r("Бенефициары: ", { bold: true }),
  r("Nutrien (NTR) и Mosaic (MOS) — крупнейшие западные производители; ICL (Израиль); K+S (Германия); Intrepid Potash (IPI). По азоту (аммиак — 23% мирового экспорта РФ): CF Industries (CF), Yara (YAR.OL)."),
]));

body.push(h2("5.4. Пшеница и продовольственная цепочка"));
body.push(p("База: 20–28% мирового экспорта; Египет, Турция и ряд стран Африки закупают в России более половины импортной пшеницы. Кейс 2022 года: с 6,40 до 12,94 доллара за месяц — и это при продолжавшихся поставках."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("12–17 долларов за бушель (×1,8–2,5); продовольственные кризисы в Египте, Ливане, Судане и политические потрясения вероятнее ценовых. "),
  r("Бенефициары: ", { bold: true }),
  r("трейдеры ADM и Bunge (BG) — перелив потоков даёт маржу; агротех Deere (DE); хедж-инструменты — ETF DBA, WEAT, CORN (прямая фьючерсная экспозиция)."),
]));

body.push(h2("5.5. Подсолнечное масло"));
body.push(p("База: Россия и Украина вместе — 70–75% мирового экспорта; вывод России устраняет примерно половину рынка. Кейс 2022 года: FOB Чёрное море ×2, до примерно 2 300 долларов за тонну, со всплеском цен пальмы и сои."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("×1,7–2,2 с перетоком в пальму и сою. "),
  r("Бенефициары: ", { bold: true }),
  r("Wilmar (Сингапур) — пальмовый трейдер; соевые переработчики ADM и Bunge; малайзийские и индонезийские плантационные группы (IOI, Sime Darby, Golden Agri)."),
]));

body.push(h2("5.6. Титан для авиации"));
body.push(p("База: ВСПМО — около 25% рынка и около 20% аэрокосмического сегмента; Boeing и Airbus диверсифицируются, но цикл переквалификации занимает годы."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("премии на титановый прокат ×2–3; срыв темпов сборки — проигравшие Boeing (BA) и Airbus (EADSY). "),
  r("Бенефициары: ", { bold: true }),
  r("западные металлурги титанового цикла ATI, Carpenter Technology (CRS), Howmet (HWM), Materion (MTRN); Timet принадлежит Berkshire — напрямую не купить."),
]));

body.push(h2("5.7. Нефть и нефтепродукты плюс танкеры"));
body.push(p("База: 11% мирового экспорта (4,8 млн баррелей в сутки), до 47% — «теневым флотом». Реалистичный шок (НПЗ плюс порты) — минус 10–20% экспорта продуктов; экстремальный — полная потеря 4–5 млн баррелей при свободных мощностях ОПЕК+ всего 5–6 млн."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("Brent 150–200 долларов (оценки 2022 года для полной потери — 150–185 и выше), рекордные дизельные спреды. "),
  r("Бенефициары: ", { bold: true }),
  r("мейджоры ExxonMobil (XOM), Chevron (CVX), Shell (SHEL), Equinor (EQNR); сервис SLB и Halliburton (HAL); главные относительные выигрыши 2022 года дали танкеры — Frontline (FRO), Scorpio Tankers (STNG), Teekay Tankers (TNK), Hafnia, TORM (TRMD): хаос маршрутов и страховых премий — это их маржа."),
]));

body.push(h2("5.8. Газ: TTF и СПГ"));
body.push(p("База: остаточные ~10% трубой (Туркстрим) и ~8% СПГ в импорте ЕС. С 2022 года Европа построила СПГ-терминалы и заполнила хранилища — та же потеря даст меньший шок."));
body.push(pRuns([
  r("Сценарий: ", { bold: true }),
  r("TTF 170–250 евро за МВт·ч (×2–3 от текущих 85; против 339 в 2022-м — ниже благодаря СПГ-инфраструктуре). "),
  r("Бенефициары: ", { bold: true }),
  r("американские liquefiers Cheniere (LNG), Venture Global (VG), NextDecade (NEXT); Equinor (норвежская труба). Плечевые UNG и BOIL опасны — декей съедает позицию."),
]));

body.push(h2("5.9. Уголь, никель, алюминий, алмазы — умеренные эффекты"));
body.push(p("Уголь: ×1,5–2; бенефициары Glencore (GLEN.L), Whitehaven (WHC.AX), New Hope (NHC.AX), Warrior Met (HCC). Никель: ×1,3–1,6 — замещение Индонезией растёт быстро; Vale, IGO. Алюминий: ×1,4–1,8 (доля РУСАЛа — 6% добычи); Alcoa (AA), Norsk Hydro (NHY.OL). Алмазы: плюс 30–50% на пике и недолго — спрос и так исторически слабый, листингованных чистых бенефициаров почти нет (Anglo American продаёт De Beers); пропускать."));

body.push(h2("5.10. Оборонные — единственный «вечный» бенефициар"));
body.push(p("Рост боевых действий означает рост заказов независимо от цен на сырьё. Кейс 2022–2026: Rheinmetall — примерно в двадцать раз (заказной портфель 62 млрд евро), сектор плюс 150–170% за 2025 год. Но с апреля 2026-го сектор находится в фазе профит-тейкинга, оценки растянуты."));
body.push(pRuns([
  r("Бенефициары: ", { bold: true }),
  r("Rheinmetall (RHM.DE), BAE Systems (BA.L), Thales (HO.PA), Leonardo (LDO.MI), Saab (SAAB-B.ST), Kongsberg (KOG.OL), Hensoldt (HAG.DE), Renk; США — Lockheed Martin (LMT), RTX, Northrop Grumman (NOC), General Dynamics (GD); ETF — ITA, XAR, PPA."),
]));

// ============ 6. Сводная таблица ============
body.push(h1("6. Сводная таблица сценария"));
body.push(caption("Таблица 3. Пики, текущие уровни, сценарные оценки и бенефициары"));
body.push(mkTable(
  ["Рынок", "Пик 2022–24", "Октябрь 2026", "Сценарий (полный шок)", "Ключевые бенефициары"],
  [
    ["Обогащение SWU", "~$200 (уже ×4)", "~$200", "×3–5 → $400–600", "LEU, CCJ, URA/URNM"],
    ["Уран спот", "$107 (02.2024)", "~$90", "$135–180", "CCJ, NXE, UEC, KAP"],
    ["Палладий", "$3 440 (03.2022)", "~$1 650", "$3 300–4 500, затем −50%", "SBSW, Impala, AAL"],
    ["Калий", "~$1 100 (Бразилия)", "$370–505", "×2,5–3,5 → $900–1 300", "NTR, MOS, ICL, K+S"],
    ["Пшеница", "$12,94", "$6,7–7,8", "$12–17", "ADM, BG, DE; DBA/WEAT"],
    ["Подсолнечное масло", "~$2 300/т", "~$1 100–1 200", "×1,7–2,2", "Wilmar, ADM, пальма"],
    ["Титан (прокат)", "премии 2022", "умеренно", "×2–3", "ATI, CRS, HWM"],
    ["Brent", "$128 (03.2022)", "~$107–125", "$150–200", "XOM, CVX, SHEL; FRO, STNG"],
    ["TTF газ", "€339 (08.2022)", "~€85", "€170–250", "LNG (Cheniere), VG, EQNR"],
    ["Уголь", "рекорды 2022", "умеренно", "×1,5–2", "GLEN, WHC, NHC, HCC"],
    ["Оборонные", "—", "Rheinmetall ×20", "заказы растут, оценки растянуты", "RHM, BA.L, SAAB-B, LMT, RTX"],
  ],
  [16, 17, 16, 23, 28],
  { small: true }
));

// ============ 7. Урок 2022 ============
body.push(h1("7. Главный урок 2022 года: спайк против структуры"));
body.push(caption("Таблица 4. Что стало с «военными» активами через 1,5–2,5 года"));
body.push(mkTable(
  ["Инструмент", "Пик шока", "Через 1,5–2,5 года", "Итог"],
  [
    ["Палладий", "$3 440", "$813 (−76%)", "ловушка замещения"],
    ["Калий", "~$1 100", "$278 (−75%)", "спайк сошёл"],
    ["Пшеница", "$12,94", "$5,07 (−61%)", "урожаи восстановились"],
    ["TTF", "€339", "€25–35 (−90%)", "СПГ-инфраструктура"],
    ["Алюминий", "$3 985", "~$2 200 (−45%)", "рецессия съела"],
    ["SWU", "—", "×4 и держится", "структурный сдвиг"],
    ["Rheinmetall", "—", "×20 и выше", "структурный сдвиг"],
    ["Centrus", "—", "×13 и выше", "структурный сдвиг"],
    ["US LNG (Cheniere)", "—", "рекордные выручки", "структурный сдвиг"],
  ],
  [22, 18, 26, 34]
));
body.push(p("Правило, которое видно из таблицы: сырьевой спайк продаётся в первые недели — часто ещё до пика, — а деньги остаются у держателей структурных сдвигов: дефицит мощностей обогащения, переоснащение армий, перестройка цепочек поставок. Бинарная ставка «на удар» без структуры почти всегда оканчивается возвратом к средней."));

// ============ 8. Архитектура позиций ============
body.push(h1("8. Архитектура позиций (образовательная рамка)"));
body.push(pRuns([
  r("1. Структурное ядро ", { bold: true }),
  r("(работает без катастрофы — уже работает): обогащение и уран (LEU, CCJ, URA/URNM), европейское переоснащение (RHM, BA.L, SAAB-B, KOG.OL, HAG.DE), СПГ (LNG), аэроматериалы (ATI, HWM). Риск — растянутые оценки и профит-тейкинг 2026 года."),
]));
body.push(pRuns([
  r("2. Хедж на обострение ", { bold: true }),
  r("(опционы «вне денег», малый капитал, готовность к минус 100%): коллы на NTR/MOS/CF (калий и азот), WEAT/CORN/DBA (зерно), SBSW (платиноиды), FRO/STNG (танкеры), BNO (нефть). Логика: если эскалация случится, опционы дают асимметрию ×5–20; если нет — премия сгорает."),
]));
body.push(pRuns([
  r("3. Лотерейные билеты: ", { bold: true }),
  r("микрокапы урана, плечевые ETF (BOIL ×2, DFEN ×3) — отрицательное математическое ожидание на горизонте из-за декея и волатильности; только для понимающих риск."),
]));
body.push(pRuns([
  r("Типовые ошибки. ", { bold: true }),
  r("Покупка после первых плюс 30% (вход в локальный пик); игнорирование экспирации опционов (шок в марте, экспирация в феврале); удержание спайков как «новой нормы» (палладий: минус 76%); плечо в первый день — в панике сначала падает всё (март 2022: индексы просели раньше, чем выросли бенефициары), и маржин-колл выносит до отскока."),
]));

// ============ 9. Ограничения для РБ ============
body.push(h1("9. Практические ограничения для резидента Беларуси"));
body.push(p("Прямого доступа нет: Interactive Brokers и брокеры ЕС, США и Великобритании не открывают счета резидентам Беларуси (санкционный комплаенс); существующие счета с белорусской привязкой — под ограничениями."));
body.push(p("Реалистичные, но не «чистые» маршруты — брокеры Казахстана, Армении, Киргизии и ОАЭ, исторически обслуживающие нерезидентов СНГ (пример — Freedom Finance Global, Казахстан); комплаенс, качество защиты инвестора и риски блокировки — на совести выбранного маршрута."));
body.push(p("Российский рынок (MOEX) формально частично доступен гражданам РБ как гражданам ЕАЭС, но санкционные ограничения на расчёты и на бумаги США и ЕС делают его неинструментом для этой темы. Налоги в РБ: доходы от продажи иностранных ценных бумаг и дивиденды облагаются подоходным налогом (13% на общих основаниях), декларирование обязательно; статус нужно уточнять с налоговым консультантом — это не налоговая консультация. Криптомаршруты регуляторно серые в РБ (майнинг запрещён, оборот ограничен резидентами ПВТ) — упоминаются как факт, не как рекомендация."));

// ============ 10. Выводы ============
body.push(h1("10. Выводы"));
body.push(p("Первое. Полный шок по всем отраслям — гипотетический; реалистичный (НПЗ, порты, логистика) уже частично отработан рынком: Brent около 107–125 долларов, TTF около 85 евро, пшеница плюс 40% за 2026 год."));
body.push(p("Второе. Максимальные мультипликаторы в остаточном сценарии — у обогащения урана (SWU ×3–5), калия (×2,5–3,5), палладия (×2–2,5 с последующим обвалом от замещения), нефти (150–200 долларов) и TTF (170–250 евро)."));
body.push(p("Третье. Легального способа «купить перед ударами» не существует; существует хедж на вероятности (опционы вне денег на бенефициарах) и структурные позиции (обогащение, оборона, СПГ), которые работают уже сейчас."));
body.push(p("Четвёртое. Главный урок 2022 года: сырьевые спайки возвращаются к средней (палладий минус 76%, калий минус 75%, TTF минус 90%), а структурные сдвиги остаются (SWU ×4, Rheinmetall ×20, Centrus выше ×13). Покупать структуру, арендовать спайк, не покупать панику."));
body.push(p("Пятое. Для резидента Беларуси инфраструктурное ограничение (доступ к западным рынкам) часто жёстче рыночного риска."));

// ============ 11. Источники ============
body.push(h1("11. Источники"));
body.push(srcItem("Trading Economics / Macrotrends — пшеница CBOT: максимум $12,94 (07.03.2022), текущие ~$6,7 (октябрь 2026)", "https://www.macrotrends.net/2534/wheat-prices-historical-chart-data"));
body.push(srcItem("Trading Economics — палладий: ATH $3 440 (03.2022), низ $813,50 (08.2024, −76%), +81,5% за 2025", "https://tradingeconomics.com/commodity/palladium"));
body.push(srcItem("Barchart (август 2025) — слом нисходящего тренда палладия; BofA — цель $2 200 к 4 кв. 2026", "https://www.barchart.com/story/news/34086620/will-palladiums-rally-continue"));
body.push(srcItem("Natural Resources Canada — калий: $328/т (июнь 2023), $278/т (октябрь 2024)", "https://www.canada.ca"));
body.push(srcItem("farmdoc daily (Университет Иллинойса, август 2026) — калий NOLA $490–505/шорт-т в 2026", "https://farmdocdaily.illinois.edu/2026/08/fertilizer-and-fuel-prices-higher-heading-into-fall-2026.html"));
body.push(srcItem("ANS (февраль 2026) — уран: спот 2025 $64–83, максимум с февраля 2024", "https://www.ans.org/news/2026-02-03/article-7731/"));
body.push(srcItem("World Nuclear Association / TradeTech — SWU ~$200 (июнь 2026), долгосрочная цена урана $97/фунт (октябрь 2026)", "https://world-nuclear.org"));
body.push(srcItem("US EIA — Uranium Marketing Annual Report 2025: $108,70/SWU (2025)", "https://www.eia.gov"));
body.push(srcItem("S&P Global (август 2022) — TTF ATH €339; текущие ~€60–86 (октябрь 2026)", "https://www.spglobal.com/latest-news/natural-gas"));
body.push(srcItem("Macrotrends — Brent: $128 (03.2022), ~$107–125 (октябрь 2026), +60% за март 2026", "https://www.macrotrends.net/2480/brent-crude-oil-prices-10-year-daily-chart"));
body.push(srcItem("Morningstar (январь 2026) — Rheinmetall +22% за 2026, около +200% с января 2025", "https://global.morningstar.com/en-gb/stocks/european-defense-stocks-rally-war-riskare-they-still-buy"));
body.push(srcItem("CNBC / MarketWatch (май 2026) — Rheinmetall ~×20 с 2022, заказы €62 млрд; профит-тейкинг сектора с апреля 2026"));
body.push(srcItem("Yahoo Finance / Macrotrends — Centrus (LEU): ~$10 (2020) → средняя за 52 недели ~$215; HALEU-контракт $900 млн (2 кв. 2026)", "https://finance.yahoo.com/quote/LEU"));
body.push(srcItem("Cameco (CCJ) — курс ~$88, капитализация ~$39,6 млрд (2026)", "https://finance.yahoo.com/quote/CCJ"));
body.push(srcItem("Первый отчёт цикла «Россия на мировых рынках» (октябрь 2026) — доли РФ: обогащение 44%, палладий 40%, калий РФ+РБ 35–40%, пшеница 20–28%, нефть 11%"));
body.push(srcItem("LME — алюминий ATH $3 985 (март 2022), никель $48 000 (08.03.2022, шорт-сквиз)", "https://www.lme.com"));
body.push(p("Отчёт носит образовательный характер, не является индивидуальной инвестиционной, юридической или налоговой рекомендацией. Упоминание тикеров — иллюстрация отраслевой экспозиции, а не предложение к покупке. Дата составления — 14 октября 2026 года."));

// ─────────────────────────────────────────────────────────────
// Assemble document
// ─────────────────────────────────────────────────────────────
const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };

function pageFooter() {
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080", font: FONT_BODY })],
    })],
  });
}

function docHeader() {
  return new Header({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "C8C8C8", space: 4 } },
      children: [new TextRun({ text: "Шок-сценарий · цены и бенефициары · не является инвестиционной рекомендацией", size: 16, color: "909090", font: FONT_HEAD })],
    })],
  });
}

const frontMatter = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 360 },
    children: [new TextRun({ text: "Содержание", bold: true, size: 32, color: P.headingColor, font: FONT_HEAD })],
  }),
  new TableOfContents("Содержание", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({
    spacing: { before: 200 },
    children: [new TextRun({
      text: "Примечание: оглавление построено на кодах полей. После редактирования документа обновите его: щёлкните по оглавлению правой кнопкой мыши и выберите «Обновить поле».",
      italics: true, size: 18, color: "888888", font: FONT_BODY,
    })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

const doc = new Document({
  creator: "ZCode",
  title: "Шок-сценарий: вывод экспортных отраслей России из строя — цены и рынки",
  styles: {
    default: {
      document: {
        run: { font: FONT_BODY, size: 24, color: P.body },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: FONT_HEAD, size: 32, bold: true, color: P.headingColor },
        paragraph: { spacing: { before: 400, after: 180, line: 312 } },
      },
      heading2: {
        run: { font: FONT_HEAD, size: 28, bold: true, color: P.headingColor },
        paragraph: { spacing: { before: 280, after: 140, line: 312 } },
      },
    },
  },
  numbering: {
    config: [{
      reference: "src-list",
      levels: [{
        level: 0,
        format: LevelFormat.DECIMAL,
        text: "%1.",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 500, hanging: 360 } } },
      }],
    }],
  },
  sections: [
    {
      properties: {
        page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } },
      },
      children: buildCoverR1({
        title: "Шок-сценарий: крах российского экспорта",
        subtitle: "Что будет с ценами, если экспортные отрасли России выведены из строя, и какие компании выигрывают от таких шоков",
        englishLabel: "SUPPLY SHOCK SCENARIO",
        metaLines: [
          "Сценарно-аналитический отчёт (стресс-тест рынков)",
          "Уран · Палладий · Калий · Зерно · Нефть · Газ · Оборона",
          "Состояние на 14 октября 2026 года · не инвестиционная рекомендация",
        ],
        footerLeft: "Сценарная справка",
        footerRight: "Октябрь 2026",
        palette: P,
      }),
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } },
      },
      footers: { default: pageFooter() },
      children: frontMatter,
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      headers: { default: docHeader() },
      footers: { default: pageFooter() },
      children: body,
    },
  ],
});

const OUT = process.argv[2] || "output.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Written:", OUT, buf.length, "bytes");
});
