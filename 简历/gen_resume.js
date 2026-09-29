const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType,
  HeadingLevel, PageBreak
} = require("docx");

// ====== Theme Colors ======
const BLUE_DARK = "1F3864";
const BLUE_MID = "2E75B6";
const GRAY_BG = "F2F2F2";
const WHITE = "FFFFFF";

// ====== Reusable Helpers ======
function sectionTitle(text) {
  return new Paragraph({
    spacing: { before: 300, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE_MID, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 28, font: "Microsoft YaHei", color: BLUE_DARK })],
  });
}

function normalPara(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 60, line: 360 },
    indent: opts.indent ? { left: 360 } : undefined,
    children: [new TextRun({ text, size: 21, font: "Microsoft YaHei", color: "333333", ...opts })],
  });
}

function boldLabel(label, value) {
  return new Paragraph({
    spacing: { after: 60, line: 360 },
    children: [
      new TextRun({ text: label, bold: true, size: 21, font: "Microsoft YaHei", color: BLUE_DARK }),
      new TextRun({ text: value, size: 21, font: "Microsoft YaHei", color: "333333" }),
    ],
  });
}

function bullet(text) {
  return new Paragraph({
    spacing: { after: 40, line: 340 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "\u2022  ", size: 21, font: "Microsoft YaHei", color: BLUE_MID }),
      new TextRun({ text, size: 21, font: "Microsoft YaHei", color: "333333" }),
    ],
  });
}

// ====== Header Table ======
const headerTable = new Table({
  width: { size: 9026, type: WidthType.DXA },
  columnWidths: [5000, 4026],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          width: { size: 5000, type: WidthType.DXA },
          margins: { top: 100, bottom: 100, left: 200, right: 100 },
          children: [
            new Paragraph({
              spacing: { after: 40 },
              children: [new TextRun({ text: "\u6D82\u4F1F\u5BCC", bold: true, size: 44, font: "Microsoft YaHei", color: BLUE_DARK })],
            }),
            new Paragraph({
              spacing: { after: 20 },
              children: [new TextRun({ text: "\u6D4B\u8BD5\u7EC4\u9577 / \u6E38\u620F\u6D4B\u8BD5\u5DE5\u7A0B\u5E08", size: 22, font: "Microsoft YaHei", color: BLUE_MID })],
            }),
          ],
        }),
        new TableCell({
          width: { size: 4026, type: WidthType.DXA },
          margins: { top: 100, bottom: 100, left: 100, right: 200 },
          verticalAlign: "center",
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              spacing: { after: 20 },
              children: [new TextRun({ text: "\u7535\u8BDD: 18379206680", size: 19, font: "Microsoft YaHei", color: "555555" })],
            }),
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              spacing: { after: 20 },
              children: [new TextRun({ text: "\u90AE\u7BB1: 1808575283@qq.com", size: 19, font: "Microsoft YaHei", color: "555555" })],
            }),
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: "\u6C5F\u897F \u00B7 \u5357\u660C | \u7537 | \u672C\u79D1", size: 19, font: "Microsoft YaHei", color: "555555" })],
            }),
          ],
        }),
      ],
    }),
  ],
});

// ====== Section: 求职意向 ======
const intentTable = new Table({
  width: { size: 9026, type: WidthType.DXA },
  columnWidths: [2256, 2256, 2257, 2257],
  rows: [
    new TableRow({
      children: [
        cell("期望岗位", "自动化测试工程师", true),
        cell("期望薪资", "10,000元/月", false),
        cell("期望城市", "广州 / 杭州", true),
        cell("工作性质", "全职", false),
      ],
    }),
  ],
});

function cell(label, value, shaded) {
  return new TableCell({
    width: { size: 2256, type: WidthType.DXA },
    shading: shaded ? { fill: GRAY_BG, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: label, bold: true, size: 18, font: "Microsoft YaHei", color: "888888" }),
          new TextRun({ text: "\n" + value, size: 20, font: "Microsoft YaHei", color: BLUE_DARK, bold: true }),
        ],
      }),
    ],
  });
}

// ====== Section: 教育背景 ======
const eduContent = [
  boldLabel("九江学院  |  软件工程（本科）  |  2019.09 - 2023.06", ""),
  bullet("主修课程：C语言、Java、Python、云计算、Unity、C#、软件测试、大数据"),
  bullet("英语水平：CET-4，能够阅读英文技术文档"),
];

// ====== Section: 工作经历 ======
const workContent = [
  boldLabel("南昌泰游网络科技有限公司  |  测试组长  |  2023.04 - 至今", ""),
  bullet("管理 2 人测试小组，负责游戏功能测试、自动化测试流程搭建与执行"),
  bullet("主导恐龙岛、巨兽岛两个项目的测试工作，涵盖功能测试、回归测试、性能测试"),
  bullet("引入 Airtest + Selenium 自动化测试框架，将回归测试效率提升 60%"),
  bullet("搭建 pytest + Allure 测试报告体系，实现测试结果可视化追踪"),
];

// ====== Section: 项目经验 ======
const projTable = new Table({
  width: { size: 9026, type: WidthType.DXA },
  columnWidths: [9026],
  rows: [
    // 恐龙岛
    new TableRow({
      children: [new TableCell({
        width: { size: 9026, type: WidthType.DXA },
        margins: { top: 100, bottom: 100, left: 200, right: 200 },
        children: [
          new Paragraph({
            spacing: { after: 40 },
            children: [new TextRun({ text: "\u6050\u9F99\u5C9B\u9879\u76EE", bold: true, size: 24, font: "Microsoft YaHei", color: BLUE_DARK })],
          }),
          new Paragraph({
            spacing: { after: 40 },
            children: [new TextRun({ text: "\u6D4B\u8BD5\u7EC4\u9577  |  \u56E2\u961F 30 \u4EBA  |  \u65E5\u6D3B 5000+", size: 19, font: "Microsoft YaHei", color: "888888" })],
          }),
          bullet("负责回放功能、领地争夺、自动挂机等核心模块的测试工作"),
          bullet("累计提交有效 Bug 2800+ 个，Bug 关闭率达 95%"),
          bullet("使用 Airtest 编写移动端自动化脚本，覆盖核心玩法回归测试"),
          bullet("设计并执行死亡回放测试用例（30条），覆盖触发机制、内容准确性、多场景等6个维度"),
        ],
      })],
    }),
    // 巨兽岛
    new TableRow({
      children: [new TableCell({
        width: { size: 9026, type: WidthType.DXA },
        margins: { top: 100, bottom: 100, left: 200, right: 200 },
        children: [
          new Paragraph({
            spacing: { after: 40 },
            children: [new TextRun({ text: "\u5DE8\u517D\u5C9B\u9879\u76EE", bold: true, size: 24, font: "Microsoft YaHei", color: BLUE_DARK })],
          }),
          new Paragraph({
            spacing: { after: 40 },
            children: [new TextRun({ text: "\u6D4B\u8BD5\u5DE5\u7A0B\u5E08", size: 19, font: "Microsoft YaHei", color: "888888" })],
          }),
          bullet("参与功能测试与兼容性测试，确保多机型适配质量"),
          bullet("配合开发团队进行 Bug 定位与回归验证"),
        ],
      })],
    }),
  ],
});

// ====== Section: 技能清单 ======
const skillData = [
  ["自动化测试", "Selenium（POM模式）、Airtest（移动端）、pytest + Allure 报告"],
  ["编程语言", "Python（主力）、Java（基础）、SQL"],
  ["数据库", "MySQL（CRUD、JOIN、子查询、索引、视图）"],
  ["操作系统", "Linux（常用命令、文件操作、权限管理）"],
  ["测试工具", "JMeter（接口测试）、PICT（成对测试用例生成）"],
  ["其他", "Git 版本控制、Jenkins CI/CD、Excel 数据驱动测试"],
];

const skillTable = new Table({
  width: { size: 9026, type: WidthType.DXA },
  columnWidths: [2000, 7026],
  rows: skillData.map((row, i) =>
    new TableRow({
      children: [
        new TableCell({
          width: { size: 2000, type: WidthType.DXA },
          shading: { fill: GRAY_BG, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: row[0], bold: true, size: 20, font: "Microsoft YaHei", color: BLUE_DARK })],
          })],
        }),
        new TableCell({
          width: { size: 7026, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({ text: row[1], size: 20, font: "Microsoft YaHei", color: "333333" })],
          })],
        }),
      ],
    })
  ),
});

// ====== Section: 自我评价 ======
const selfEval = [
  bullet("做事沉稳精炼，具备良好的问题分析与解决能力，善于从测试角度推动产品质量提升"),
  bullet("乐于学习新技术，业余持续学习自动化测试、AI测试等前沿方向"),
  bullet("善于团队沟通协作，测试组长经验，能够合理分配任务并带领团队达成质量目标"),
];

// ====== Assemble Document ======
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Microsoft YaHei", size: 21 } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1000, right: 1440, bottom: 1000, left: 1440 },
      },
    },
    children: [
      headerTable,
      new Paragraph({ spacing: { after: 80 } }),
      sectionTitle("求职意向"),
      intentTable,
      sectionTitle("教育背景"),
      ...eduContent,
      sectionTitle("工作经历"),
      ...workContent,
      sectionTitle("项目经验"),
      projTable,
      sectionTitle("技能清单"),
      skillTable,
      sectionTitle("自我评价"),
      ...selfEval,
    ],
  }],
});

const outDir = "C:/Users/Administrator/WorkBuddy/Claw/简历";
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const outPath = outDir + "/涂伟富_简历.docx";

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("Done: " + outPath);
});
