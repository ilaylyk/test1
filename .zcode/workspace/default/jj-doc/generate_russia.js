// Россия на мировых рынках: фактические монополии и существенные доли — аналитический отчёт (Russian)
// Recipe: R1 (Pure Paragraph Left), steel/bronze palette, per docx skill design system.
// Builder reused from generate_luch.js pipeline (validated 18/18 pass on 08.10.2026).
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, SectionType, TableLayoutType,
  TableOfContents, PageBreak, ExternalHyperlink, LevelFormat, ImageRun,
} = require("docx");
const fs = require("fs");
const path = require("path");

const P = {
  bg: "1E2A3A",
  accent: "B3763B",
  cover: { titleColor: "FFFFFF", subtitleColor: "C3CAD2", metaColor: "9AA3AD", footerColor: "6E7680" },
  table: { headerBg: "B3763B", headerText: "FFFFFF", innerLine: "D8CCBB", surface: "F4EEE4" },
  headingColor: "1E2A3A",
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
body.push(p("Россия остаётся незаменимым поставщиком на узком круге мировых рынков и крупным игроком — на широком. К началу 2026 года картина выглядит так."));
body.push(pRuns([
  r("Фактические монополии (выше 40% мирового рынка). ", { bold: true }),
  r("Обогащение урана — около 40–46% мировых мощностей; палладий — около 40% мировой добычи; янтарь-сырец — около 65% рынка при более чем 90% мировых запасов; калийные удобрения — совместно с Беларусью около 35–40% мировой торговли; строительство атомных блоков — около 37% всех строящихся реакторов мира по российским проектам."),
]));
body.push(pRuns([
  r("Рыночное лидерство (20–40%). ", { bold: true }),
  r("Пшеница — первое место в мире, около 20–28% мирового экспорта; подсолнечное масло — первое место с сезона 2025/26, впервые за примерно 20 лет обойдя Украину; минеральные удобрения в целом — крупнейший экспортёр мира, около 20% мировой торговли; титан для авиации (ВСПМО-АВИСМА) — 20–25%; алмазы — первое место по стоимости добычи третий год подряд (около 30% по объёму); высокосортный никель — первое место в классе 1; минтай в Европе — 43% рынка."),
]));
body.push(pRuns([
  r("Значимые доли (5–20%). ", { bold: true }),
  r("Нефть — второй экспортёр мира (около 11% экспорта); СПГ — четвёртый (7–8%); уголь — третий (12–15%); платина — около 10%; ячмень, горох, пиломатериалы, треска."),
]));
body.push(pRuns([
  r("Падающие позиции. ", { bold: true }),
  r("Трубопроводный газ в ЕС (с примерно 40% в 2021 году до около 10% в 2025-м), вооружения (смещена со второго места на третье, доля упала примерно с 21% до 8%), космические запуски, ракетные двигатели, поставки программного обеспечения информационной безопасности."),
]));
body.push(p("Главный вывод: санкционное давление 2022–2026 годов заметно сократило доли России на санкционно-чувствительных рынках — газ в ЕС, вооружения, СПГ, — но сырьевые монополии устояли. По палладию, обогащённому урану, алмазам и удобрениям альтернативы либо отсутствуют, либо создаются годами и требуют миллиардов долларов."));

// ============ 2. Методология и сводная таблица ============
body.push(h1("2. Методология и сводная картина"));
body.push(h2("2.1. Градации"));
body.push(p("В отчёте используются три градации доли рынка, от которых зависит и оценка замещаемости поставщика."));
body.push(caption("Таблица 1. Градации рыночных позиций"));
body.push(mkTable(
  ["Градация", "Критерий", "Суть"],
  [
    ["Фактическая монополия", "более 40% рынка", "замена поставщика требует лет и капитала либо невозможна без потери качества"],
    ["Доминирование / лидерство", "20–40%", "альтернативы есть, но замена заметно дорожает или снижает качество"],
    ["Значимая доля", "5–20%", "рынок диверсифицирован, сбой поставщика ощутим, но заменим"],
  ],
  [26, 22, 52]
));
body.push(p("«Доля рынка» может считаться от добычи, от экспорта или от мощностей — цифры различаются; в таблице 2 указано, от какой базы считается доля. Источники — Reuters, SIPRI, EIA, USDA, Всемирная ядерная ассоциация, S&P Global, Rapaport, Natural Resources Canada, CREA; корпоративные данные (Росатом, «Норникель», ТВЭЛ) помечены как заявления компаний. Данные в основном за 2024–2025 годы; полная датировка — в разделе источников."));
body.push(h2("2.2. Сводная таблица по отраслям"));
body.push(caption("Таблица 2. Доли России на ключевых мировых рынках (2024–2026)"));
body.push(mkTable(
  ["Рынок", "Доля России", "Место", "Динамика", "Заменяемость для Запада"],
  [
    ["Обогащение урана", "~40–46% мощностей", "1", "стабильно", "очень низкая до 2028"],
    ["Палладий (добыча)", "~40%", "1", "медленное снижение", "низкая (замена платиной возможна)"],
    ["Янтарь-сырец", "~65% рынка", "1", "стабильно", "практически нет"],
    ["Калийные удобрения (РФ+РБ)", "~35–40% торговли", "1–2", "восстановление после 2022", "средняя (Канада расширяется)"],
    ["Строительство АЭС", "~37% строящихся блоков", "1", "рост портфеля", "низкая в среднесроке"],
    ["Пшеница (экспорт)", "~20–28%", "1", "около рекордных объёмов", "высокая"],
    ["Подсолнечное масло", "~25–38%", "1", "рост, обошла Украину в 2025/26", "средняя"],
    ["Удобрения в целом", "~20% торговли", "1", "рост, цель 25% к 2030", "средняя"],
    ["Титан для авиации", "~20–25%", "1", "снижение, уход Boeing/Airbus", "низкая в краткосроке"],
    ["Алмазы", "~30% добычи", "1", "переориентация на Азию", "средняя"],
    ["Никель класса 1", "~14% выпуска", "1", "стабильно", "средняя"],
    ["Минтай (рынок Европы)", "~43%", "1", "рост, обошла США в 2025", "средняя"],
    ["Нефть (экспорт)", "~11%", "2", "объёмы держатся", "высокая"],
    ["СПГ", "~7–8%", "4", "снижение (−8% в 2025)", "высокая"],
    ["Уголь (экспорт)", "~12–15%", "3", "снижение", "высокая"],
    ["Платина (добыча)", "~10%", "3", "стабильно", "средняя"],
    ["Вооружения (экспорт)", "~7–8%", "3", "обвал, −64% за пять лет", "высокая"],
    ["Газ в ЕС по трубопроводам", "~10% (было ~40%)", "—", "обвал, −44% в 2025", "уже заменена"],
  ],
  [23, 18, 11, 24, 24],
  { small: true }
));
body.push(h2("2.3. Наглядное сопоставление"));
body.push(caption("Диаграмма 1. Доли России на ключевых мировых рынках"));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 60 },
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(__dirname, "chart_russia.png")),
    transformation: { width: 580, height: 376 },
  })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 160 },
  children: [new TextRun({
    text: "Источники и базы расчёта — таблица 2. Цвет: бронзовый — 40% и выше (фактическая монополия), тёмно-песочный — 20–40%, серый — ниже 20%.",
    italics: true, size: 18, color: "888888", font: FONT_BODY,
  })],
}));

// ============ 3. Фактические монополии ============
body.push(h1("3. Фактические монополии"));
body.push(h2("3.1. Обогащение урана — ядро атомной монополии"));
body.push(p("Росатом (через ТВЭЛ и «Техснабэкспорт») контролирует около 44% мировых мощностей по обогащению урана — это наиболее часто цитируемая цифра (Reuters, 2025); оценки варьируются от примерно 40% (Bellona, 2026) до 46% (FIIA). Дополнительно — около 38% рынка услуг конверсии."));
body.push(pRuns([
  r("Топливо. ", { bold: true }),
  r("ТВЭЛ обеспечивает около 17% мирового рынка ядерного топлива — цифра устойчива больше десятилетия; топливом снабжаются около 75 энергоблоков в 15 странах, включая западные реакторы PWR в Чехии, Словакии, Финляндии, Швеции и на Украине."),
]));
body.push(pRuns([
  r("США — крупнейший покупатель. ", { bold: true }),
  r("До запрета Россия закрывала около 25% потребности американских реакторов в обогащённом уране. Закон «Prohibiting Russian Uranium Imports Act» действует с августа 2024 года, но с исключениями (waivers): в 2025 году доля России в импорте обогащённого урана США снова составила 24,5% — западных несанкционных мощностей хронически не хватает. Полный отказ запланирован лишь к 2028 году."),
]));
body.push(p("Ключевой рычаг — не добыча (Россия лишь шестой добытчик урана в мире), а средний и нижний переделы: конверсия и обогащение. Это, пожалуй, единственная отрасль, где Россия — подлинный стратегический монополист для Запада: нефтепродукты заменяются перенаправлением танкеров, а центрифужное обогащение — нет."));
body.push(h2("3.2. Палладий"));
body.push(p("«Норникель» — крупнейший в мире производитель палладия: около 40–41% мировой добычи (2,73 млн унций в 2025 году). Вместе с ЮАР (также около 40%) на две страны приходится около 80% первичного палладия. С учётом вторичного металла доля России в общемировом предложении — около 25%."));
body.push(p("Палладий критичен для автокатализаторов бензиновых двигателей и электроники (керамические конденсаторы MLCC выпускаются сотнями миллиардов штук в год). Прямого санкционного запрета на палладий нет; в 2025 году США ввели пошлины на слитки, задев в том числе палладий, переработанный в Швейцарии, — рынок отреагировал всплеском цен. Дефицит рынка палладия в 2025 году — около 416 тысяч унций против 218 тысяч в 2024-м. Замена платиной технически возможна, но требует перенастройки автокаталитических производств и лет на переход."));
body.push(h2("3.3. Янтарь"));
body.push(p("Калининградский янтарный комбинат (посёлок Янтарный) — крупнейший в мире добытчик янтаря-сырца: около 65% мирового рынка, порядка 400 тонн в год. При этом более 90% мировых разведанных запасов янтаря сосредоточено именно в самбийском месторождении Калининградской области. Это классическая ресурсная монополия: запасы физически сосредоточены в одной точке земного шара и невоспроизводимы."));
body.push(quote("Нюанс: доминирование России — в добыче сырца. Обработку и экспорт готовых изделий (бижутерия, ювелирные изделия) монополизировала Польша — около 60% мирового экспорта обработанного янтаря, перерабатывающего в том числе российский сырец."));
body.push(h2("3.4. Калийные удобрения: дуополия России и Беларуси"));
body.push(p("Рынок калийных солей — фактически двухполюсный. Канада держит около 35–40% мировой торговли; далее Беларусь («Беларуськалий» и Белорусская калийная компания — около 19% мирового экспорта, второе место) и Россия («Уралкалий» — третье место, около 15%). Вместе РФ и РБ — около 35–40% мировой торговли калием (оценка Объединённого исследовательского центра Еврокомиссии для 2019 года — 41%)."));
body.push(p("После санкций 2022 года экспорт проседал, но выравнялся: к концу 2025 года Беларусь восстановила около 88% досанкционных объёмов, а Минэнерго Канады оценивает её долю в мировом экспорте в 18,7%. Для Беларуси это самостоятельная позиция: «Беларуськалий» — не сателлит российского экспорта, а второй полюс рынка."));
body.push(quote("Историческая справка: до 2013 года обе страны торговали через единый картель БКК, дважды за 2000-е взвинчивавший мировые цены. Сегодня они конкурируют, но по-прежнему вместе контролируют треть мирового рынка."));
body.push(h2("3.5. Строительство атомных электростанций"));
body.push(p("Росатом — первое место в мире по количеству строящихся реакторов: по российским проектам (ВВЭР) строится около 37% всех реакторов мира — порядка 30 блоков из примерно 80 строящихся (по данным самого Росатома; независимая проверка затруднена). Портфель зарубежных заказов: подписаны соглашения на 22 реактора в семи странах — Турция (Аккую), Бангладеш (Руппур), Египет (Эль-Дабаа), Китай, Индия (Куданкулам), Иран, Венгрия (Пакш-II); ещё 60–70 блоков на стадии переговоров."));
body.push(p("Особенность модели — «строительство плюс топливо плюс сервис на 60 лет»: блок, построенный Росатомом, десятилетиями потребляет российское топливо и сервис, замыкая цикл из раздела 3.1. Оговорка: независимые аналитики (OSW) отмечают, что часть подписанных проектов буксует из-за финансирования, санкций и срывов сроков; тем не менее по количеству реально строящихся блоков Росатом вне конкуренции. Дополнительный сигнал — выбор консорциума с участием Росатома для первой АЭС Казахстана."));

// ============ 4. Продовольственное лидерство ============
body.push(h1("4. Продовольственное лидерство"));
body.push(h2("4.1. Пшеница и зерновые"));
body.push(p("Россия — первый экспортёр пшеницы в мире с 2016 года, и разрыв с конкурентами (ЕС, Канада, Австралия, США) почти каждый сезон растёт. Рекорд сезона 2023/24 — 55,4 млн тонн, около 28% мировой торговли пшеницей. Прогноз на 2025/26 — около 43 млн тонн (SovEcon), то есть 20–25% мирового экспорта: сезон слабее из-за снижения урожая, но лидерство сохраняется с большим отрывом."));
body.push(p("Критическая зависимость сложилась у отдельных стран: Египет, Турция, Судан и ряд стран Африки и Ближнего Востока закупают более половины импортной пшеницы в России. Это главный геополитический рычаг продовольственного типа — «зерновая сделка» 2022–2023 годов показала чувствительность мировых цен к одному экспортёру."));
body.push(pRuns([
  r("Смежные позиции: ", { bold: true }),
  r("горох — Россия — первый экспортёр мира (в 2023/24 заняла 49% китайского импорта гороха, вытеснив Канаду); лён (льносемена) — первое место в мире, оттеснив Канаду; ячмень — стабильный третий экспортёр, примерно 15–17% мирового экспорта."),
]));
body.push(h2("4.2. Подсолнечное масло: смена лидера"));
body.push(p("В сезоне 2025/26 Россия впервые примерно за 20 лет обогнала Украину и стала первым экспортёром подсолнечного масла с рекордными 5 млн тонн — это 25–38% мирового рынка (оценки различаются: около 25% в среднем за несколько лет и до 38% в текущем сезоне). Вместе Россия и Украина дают 70–75% мирового экспорта подсолнечного масла — классическая региональная дуополия чернозёмного пояса. Также Россия вышла на 11 млн тонн экспорта масел и жиров всех видов — крупнейший показатель в своей истории."));
body.push(h2("4.3. Минеральные удобрения в целом"));
body.push(p("Россия — крупнейший экспортёр удобрений в мире: около 20% мировой торговли в 2025 году; в денежном выражении — 15,1 млрд долларов в 2024 году, первое место среди 177 стран. По продуктам: аммиак — около 23% мирового экспорта, карбамид — около 14%, фосфорные удобрения — около 10%, калийные — см. раздел 3.4."));
body.push(p("Отрасль не попала под прямые санкции — она признана критичной для мировой продовольственной безопасности, и отраслевые ассоциации анонсировали цель — 25% мирового рынка к 2030 году. Это редкий случай, когда доля России после 2022 года растёт."));
body.push(h2("4.4. Рыба и морепродукты"));
body.push(p("Минтай: Россия — крупнейший в мире добытчик; в 2025 году заняла 43,4% европейского рынка минтаевого филе (США — 36%, Китай — 20,5%) и впервые обошла США в глобальных продажах минтая. Треска: Россия и Норвегия делят квоты Баренцева моря — фактически дуополия в атлантической треске. Китай: в 2025 году Россия поставила рыбы на 3,42 млрд долларов — 14,4% китайского импорта морепродуктов."));

// ============ 5. Металлы и минералы ============
body.push(h1("5. Металлы и минералы"));
body.push(h2("5.1. Титан: ВСПМО-АВИСМА"));
body.push(p("Верхнесалдинское объединение — крупнейший в мире производитель титановых изделий: около 25% мирового рынка титана и около 20% сегмента аэрокосмического титана (2025, Global Market Insights; до 2022 года доля была выше — до 30%)."));
body.push(p("До войны Boeing закупал в ВСПМО до 80% своего титана, Airbus — около 60%. Это был хрестоматийный пример санкционной невозможности: санкции введены, а самолёты без российского титана не строятся. Boeing в мае 2024 года продлил контракт с ВСПМО; Airbus публично заявил о планах полного отказа. Западные альтернативы (ATI, TIMET, Howmet — суммарно около 53% аэрокосмического сегмента) наращивают мощности, но передел от сляба до штамповки с сертификацией для авиакомпаний занимает годы. Главный факт: ВСПМО остаётся первым в мире, несмотря на санкции против материнской «Ростеха», — альтернативы сопоставимого масштаба в сертифицированном цикле пока нет."));
body.push(h2("5.2. Алмазы"));
body.push(p("АЛРОСА (около 95% российской добычи) — первая в мире по объёму: около 30% мировой добычи, 31,5 млн карат в 2025 году; в денежном выражении 2,72 млрд долларов — первое место третий год подряд (Rapaport). Вместе с De Beers (около 30%) АЛРОСА формирует дуополию добычи, задающую цены всему рынку."));
body.push(p("С января 2024 года действует полный запрет G7 на российские необработанные алмазы, включая трассировку бриллиантов, огранённых в третьих странах (главный реэкспортёр — индийский Сурат). Тем не менее в 2025 году Россия сохранила лидерство по стоимости: продажи переориентированы на ОАЭ, Индию и Китай. Мировая добыча в каратах при этом падает (минус 8% за 2025 год), и доля РФ в ней лишь растёт."));
body.push(h2("5.3. Никель, платина, алюминий, медь"));
body.push(p("Никель: «Норникель» — мировой лидер по высокосортному никелю (класс 1, нужен для аккумуляторов и нержавеющей стали) — около 14% мирового выпуска и 96% российской добычи. Платина: около 10% мировой добычи, третье место после ЮАР и Зимбабве; родий — значимый поставщик (основной — ЮАР). Алюминий: РУСАЛ — крупнейший производитель вне Китая, около 6% мирового выпуска первичного алюминия. Медь: Россия — в первом десятке (около 4% мировой добычи), заметно ниже, чем по платиноидам."));

// ============ 6. Энергоресурсы ============
body.push(h1("6. Энергоресурсы"));
body.push(h2("6.1. Нефть и нефтепродукты"));
body.push(p("Россия — второй экспортёр нефти в мире после Саудовской Аравии: около 11% мирового экспорта, порядка 4,8 млн баррелей в сутки; добыча в 2025 году всего на 2,5% ниже довоенного уровня 2021-го. Санкции ЕС и G7 (эмбарго плюс потолок цен 60 долларов) изменили логистику, а не объёмы: до 47% экспорта идёт «теневым флотом» (танкеры вне западной страховки), дисконт Urals к Brent в 2024–2025 годах — 10–15 долларов."));
body.push(p("Переориентация на Азию: в 2025–2026 годах доля России в морских поставках нефти в Китай достигала 23% (сорт ESPO); Китай — покупатель более половины российских углеводородных доходов. Нефтепродукты: Россия — один из двух крупнейших экспортёров дизельного топлива в мире (вместе с США) и ключевой поставщик мазута; после эмбарго ЕС продажи переориентированы на Турцию, Индию, Африку и Бразилию."));
body.push(h2("6.2. Газ: две противоположные траектории"));
body.push(pRuns([
  r("Трубопроводный газ в Европу — обвал. ", { bold: true }),
  r("С примерно 40% рынка ЕС в 2021 году до около 10% в 2025-м. Транзит через Украину остановлен 31 декабря 2024 года, «Северные потоки» разрушены в 2022-м. Остался только «Турецкий поток» — около 18 млрд кубометров в 2025 году (минус 44% за год, минимум с середины 1970-х). В марте 2026 года ЕС принял закон о полном отказе от российского газа."),
]));
body.push(pRuns([
  r("СПГ и добыча — устойчиво. ", { bold: true }),
  r("Россия — четвёртый экспортёр СПГ в мире (около 47 млн тонн в 2024 году, 7–8% мирового рынка) после США, Катара и Австралии. В 2025 году экспорт СПГ упал на 8% (санкции против «Арктик СПГ-2», запрет ЕС на перегрузку), но доля в мировой добыче газа остаётся около 15%. Новые мощности (Амурский завод, «Арктик СПГ-2») нацелены на Азию."),
]));
body.push(h2("6.3. Уголь"));
body.push(p("Россия — третий экспортёр угля в мире (18,5 млрд долларов в 2025 году, после Австралии и Индонезии): 12–15% мировой торговли, в металлургическом угле — около 12%. Динамика отрицательная: доходы морского экспорта упали на 22% в 2024 году и продолжали снижаться в 2025-м на фоне общего спада мирового угольного рынка — Китай сокращает импорт."));

// ============ 7. Вооружения ============
body.push(h1("7. Вооружения: со второго места в третью лигу"));
body.push(p("Самое яркое падение за период наблюдений. В 2016–2020 годах Россия — второй экспортёр вооружений с 20–21% мирового рынка. По данным SIPRI за 2020–2024 годы (март 2025) — уже третье место с 7,8%: Франция впервые с 1990-х обошла Россию. По данным за 2021–2025 годы (SIPRI, март 2026) Франция закрепилась на втором месте (9,8%), а российский экспорт рухнул на 64% за пятилетку."));
body.push(p("Причины: собственные потребности фронта, санкции на компоненты, опасения покупателей перед вторичными санкциями, утрата маркетинговых площадок. Исторические рынки — Индия, Вьетнам, Алжир, Китай — сокращают закупки или диверсифицируются; исключение — Индия, сохраняющая высокую зависимость от российских платформ (Су-30, С-400)."));
body.push(p("Контраст с атомной отраслью показателен: экспорт вооружений — высококонкурентный рынок с сильными продавцами (США — 43%, Франция — около 10%), и там Россия проиграла. Рынок обогащения и строительства АЭС — рынок с двумя-тремя игроками, и там позиции держатся."));

// ============ 8. Утраченные позиции ============
body.push(h1("8. Утраченные и сокращающиеся позиции"));
body.push(caption("Таблица 3. Что Россия потеряла с 2021 года"));
body.push(mkTable(
  ["Позиция", "Было", "Стало"],
  [
    ["Трубопроводный газ в ЕС", "~40% импорта ЕС (2021)", "~10% (2025); закон ЕС о полном отказе (март 2026)"],
    ["Ракетные двигатели РД-180/РД-181", "монополия для Atlas V и Antares (США)", "поставки прекращены; ULA перешла на Vulcan (BE-4), Northrop — на американские двигатели"],
    ["Пилотируемые запуски для NASA", "монополия «Союзов» (2011–2020)", "Crew Dragon с 2020; ESA свернула сотрудничество в 2022 (ExoMars)"],
    ["Информационная безопасность", "«Лаборатория Касперского» — мировой топ-бренд", "запрет продаж в США (июнь 2024), уход с западных рынков"],
    ["Титан для Airbus", "~60% титана Airbus", "заявлен полный отказ (переход к 2028); Boeing пока продлевает"],
  ],
  [26, 34, 40]
));
body.push(p("Общий паттерн: теряются рынки, где продукт или услуга стандартизованы и есть поставщики-конкуренты; удерживаются рынки с концентрацией предложения и долгим циклом замены."));

// ============ 9. Санкционное давление ============
body.push(h1("9. Санкционное давление: результаты к 2026 году"));
body.push(caption("Таблица 4. Механизмы давления и фактические результаты"));
body.push(mkTable(
  ["Рынок", "Механизм давления", "Результат к 2026 году"],
  [
    ["Обогащённый уран", "запрет США (2024) с исключениями", "доля РФ в импорте США в 2025 — снова ~24,5%; реальный отказ лишь к 2028"],
    ["Алмазы", "запрет G7 (2024) + трассировка", "РФ сохранила первое место по стоимости; переориентация на ОАЭ, Индию, Китай"],
    ["Нефть", "эмбарго ЕС + потолок цен", "объёмы почти не упали; дисконт и «теневой флот» (до 47% перевозок)"],
    ["Палладий", "пошлины США на слитки", "всплеск цен; прямой запрет отсутствует"],
    ["Удобрения", "прямых санкций нет", "доля растёт; цель — 25% к 2030"],
    ["Газ (труба, ЕС)", "отказ покупателя + разрушение «Северных потоков»", "единственный случай фактического вытеснения"],
    ["СПГ (ЕС)", "запрет перегрузки (2025)", "минус 8% экспорта, но без обвала; продажи в Азию"],
    ["Вооружения", "вторичные санкции + потребности фронта", "самое сильное падение: −64% за пять лет"],
  ],
  [20, 36, 44]
));
body.push(p("Вывод раздела: там, где Запад действует рыночными инструментами (нефть, СПГ, алмазы), доли России снижаются медленно — через дисконты и переориентацию потоков, а не через уход с рынка. Физически вытеснен только трубопроводный газ. А уран, палладий и титан показали, что часть зависимостей не снимается политическими решениями на горизонте трёх-пяти лет."));

// ============ 10. Почему монополии устойчивы ============
body.push(h1("10. Почему монополии устойчивы"));
body.push(pRuns([
  r("1. Геологическая рента. ", { bold: true }),
  r("Норильские сульфидные руды (палладий и никель попутно), якутские кимберлиты, самбийский янтароносный горизонт, чернозём — запасы физически локализованы и невоспроизводимы."),
]));
body.push(pRuns([
  r("2. Советское наследие с барьером входа. ", { bold: true }),
  r("Атомный цикл (конверсия, обогащение, топливо, станции), ВСПМО (построен как монополист СЭВ), единая инфраструктура — активы, которые конкурент должен строить десятилетиями."),
]));
body.push(pRuns([
  r("3. Низкая себестоимость. ", { bold: true }),
  r("Дешёвая собственная энергия делает добычу и обогащение конкурентными даже при дисконтах и санкционных издержках."),
]));
body.push(pRuns([
  r("4. Замкнутость цикла. ", { bold: true }),
  r("Построенная Росатомом станция — это 60 лет потребления российского топлива и сервиса: монополия усиливает саму себя."),
]));
body.push(pRuns([
  r("5. Готовность Запада платить за стабильность. ", { bold: true }),
  r("Boeing продлевает контракт с ВСПМО, американские энергокомпании берут исключения на российский уран — заменитель дороже или хуже, и покупатель это знает."),
]));

// ============ 11. Выводы ============
body.push(h1("11. Выводы"));
body.push(p("Первое. Подлинные монополии России на мировом рынке 2026 года: обогащение урана (около 44%), палладий (около 40%), янтарь-сырец (около 65%), совместная с Беларусью калийная дуополия (35–40%), атомное строительство (около 37% строящихся блоков мира)."));
body.push(p("Второе. Устойчивое продовольственное лидерство: пшеница (20–28% мирового экспорта), подсолнечное масло (первое место с 2025/26), горох, лён, удобрения (первое место). Эти доли политически значимы — продовольственная безопасность Египта, Турции, стран Африки, — но легко заменимы при наличии времени: дефицита продукта не возникнет, возникнет рост цен."));
body.push(p("Третье. Технологические ниши труднее всего поддаются санкционному вытеснению: уран, титан и палладий Запад покупает уже годы после введения собственных запретов."));
body.push(p("Четвёртое. Проигранные фронты: вооружения (третье место, доля упала втрое), трубопроводный газ в ЕС (вытеснен), космические запуски, антивирусное программное обеспечение."));
body.push(p("Пятое. Общий тренд 2022–2026 годов — медленная эрозия долей, а не крах: объёмы экспорта переориентируются с Запада на Азию (Китай уже покупает половину углеводородных доходов), и мировые цены, а не санкции, остаются главным ограничителем российских доходов."));

// ============ 12. Источники ============
body.push(h1("12. Источники"));
body.push(srcItem("Reuters — «Russia's Rosatom starts development of uranium deposit in Eastern Siberia» (август 2025): 44% мировых мощностей обогащения", "https://www.reuters.com/business/energy/russias-rosatom-starts-development-uranium-deposit-eastern-siberia-2025-08-08"));
body.push(srcItem("FIIA — «Russia and Kazakhstan in the global nuclear sector»: 46% обогащение, 38% конверсия", "https://fiia.fi/en/publication/russia-and-kazakhstan-in-the-global-nuclear-sector"));
body.push(srcItem("Bellona — «The New Nuclear Digest» (март 2026): около 40% обогащения, экспортные тренды", "https://bellona.org/news/nuclear-issues/2026-03-rosatoms-exports-slip-china-buys-up-russian-fuel-and-the-us-boosts-enrichment-the-new-nuclear-digest-is-out"));
body.push(srcItem("World Nuclear Association — «Russia's Nuclear Fuel Cycle» (сентябрь 2026): 17% рынка топлива ТВЭЛ", "https://world-nuclear.org/information-library/country-profiles/countries-o-s/russia-nuclear-fuel-cycle"));
body.push(srcItem("US DOE — «Russian Uranium Ban Waiver Guidance»: закон о запрете импорта с августа 2024", "https://www.energy.gov/ne/russian-uranium-ban-waiver-guidance"));
body.push(srcItem("World Nuclear Association — «Plans for New Reactors Worldwide»: около 80 строящихся реакторов", "https://world-nuclear.org/information-library/current-and-future-generation/plans-for-new-reactors-worldwide"));
body.push(srcItem("OSW Commentary (январь 2026): 22 реактора в семи странах по соглашениям Росатома", "https://www.osw.waw.pl"));
body.push(srcItem("«Норникель» — пресс-релиз за 2025 год (январь 2026) и обзоры рынка металлов", "https://nornickel.com/news-and-media/press-releases-and-news/nornickel-announces-consolidated-production-results-for-fy2025"));
body.push(srcItem("S&P Global Ratings — VSMPO-AVISMA «BB+»: крупнейший производитель титана, около 25% рынка", "https://www.spglobal.com/ratings/en/regulatory/article/-/view/sourceId/11893653"));
body.push(srcItem("Rapaport — «Russia Largest Rough Producer by Value in 2025 for Third Year» (июль 2026)", "https://rapaport.com/news/russia-largest-rough-producer-by-value-in-2025-for-third-year"));
body.push(srcItem("SIPRI — Fact Sheet «Trends in International Arms Transfers, 2025» (март 2026): Франция — 9,8%, российский экспорт минус 64%", "https://www.sipri.org/publications/2026/sipri-fact-sheets/trends-international-arms-transfers-2025"));
body.push(srcItem("SIPRI — пресс-релиз (март 2026): Россия — третье место с 7,8% (2020–2024)", "https://www.sipri.org/media/press-release/2026/global-arms-flows-jump-nearly-10-cent-european-demand-soars"));
body.push(srcItem("US EIA — Country Analysis Brief: Russia (июль 2025): второй экспортёр нефти, около 11% (4,8 млн барр./сут)", "https://www.eia.gov/international/analysis/country/RUS"));
body.push(srcItem("CREA — «Monthly analysis of Russian fossil fuel exports» (сентябрь 2026): доля в импорте Китая, теневой флот", "https://energyandcleanair.org/august-2026-monthly-analysis-of-russian-fossil-fuel-exports-and-sanctions"));
body.push(srcItem("SEALA — «LNG Export by Russia»: 47,2 млн тонн (2024), четвёртое место в мире", "https://www.seala.ai/lngstatistics/lng-export-by-russia"));
body.push(srcItem("Reuters — «Global coal exports post rare decline in 2025» (декабрь 2025)", "https://www.reuters.com/markets/commodities/global-coal-exports-post-rare-decline-2025-china-cuts-2025-12-16"));
body.push(srcItem("Reuters — «Russia eyes more sunflower oil exports to India» (сентябрь 2025): рекорд 5 млн тонн, первое место", "https://www.reuters.com/business/energy/russia-eyes-more-sunflower-oil-exports-india-2025-09-26"));
body.push(srcItem("Reuters — «Russia has surplus peas after failing to boost exports to China» (декабрь 2025): 49% китайского импорта гороха", "https://www.reuters.com/world/china/russia-has-surplus-peas-after-failing-boost-exports-china-analysts-say-2025-12-11"));
body.push(srcItem("Reuters — «Russia's pipeline gas exports to Europe fall by 44%» (декабрь 2025)", "https://www.reuters.com/business/energy/russias-pipeline-gas-exports-europe-fall-by-44-lowest-decades-2025-12-30"));
body.push(srcItem("Reuters — «Russian fertilizer producers target 25% global market share by 2030» (июль 2025)", "https://www.reuters.com/world/china/russian-fertilizer-producers-target-25-global-market-share-by-2030-lobby-group-2025-07-17"));
body.push(srcItem("Natural Resources Canada (январь 2026) / Investing News: Беларусь — 18,7% мирового экспорта калия, второе место", "https://investingnews.com/daily/resource-investing/agriculture-investing/potash-investing/top-potash-countries-by-production"));
body.push(srcItem("SeafoodNews / Interfax (2026): минтай — 43,4% рынка Европы, обгон США; экспорт рыбы в Китай — 3,42 млрд долларов"));
body.push(srcItem("USDA FAS — «Russia Grain and Oilseed Exports Expand»", "https://www.fas.usda.gov/data/russia-grain-and-oilseed-exports-expand"));
body.push(srcItem("SovEcon (июль 2025): прогноз 42,9 млн тонн пшеницы в сезоне 2025/26"));
body.push(p("Корпоративные данные (Росатом, «Норникель», ТВЭЛ, Калининградский янтарный комбинат) помечены как заявления компаний и могут смещаться в сторону завышения долей. Цифры по калийным удобрениям даны диапазоном из-за разных баз расчёта. Дата составления — 14 октября 2026 года."));

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
      children: [new TextRun({ text: "Россия на мировых рынках · монополии и доли · аналитический отчёт", size: 16, color: "909090", font: FONT_HEAD })],
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
  title: "Россия на мировых рынках: фактические монополии и существенные доли — аналитический отчёт",
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
        title: "Россия на мировых рынках",
        subtitle: "Фактические монополии и существенные доли: уран, палладий, калий, пшеница, титан, алмазы",
        englishLabel: "RUSSIA IN GLOBAL MARKETS",
        metaLines: [
          "Аналитический отчёт по открытым источникам",
          "Энергетика · Атомная отрасль · Металлы и минералы · АПК · ВПК",
          "Состояние на 14 октября 2026 года",
        ],
        footerLeft: "Аналитическая справка",
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
