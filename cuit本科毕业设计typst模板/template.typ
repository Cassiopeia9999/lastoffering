// 版权说明
// 作者：尹庆（成都信息工程大学）
// 邮箱：qyin@cuit.edu.cn
// 如在使用本模板过程中发现问题、存在疑问或有改进建议，欢迎通过电子邮件联系作者。
// 本模板主要用于学习、教学与科研场景；未经许可不得用于商业用途。
// 允许在保留本说明的前提下进行非商业性转载与修改；若需其他用途请事先取得授权。
// 如需引用或分发，请一并保留本版权说明。

// 引入中文伪粗体扩展
#import "@preview/cuti:0.3.0": show-cn-fakebold
// 引入去除 CJK 换行空格的扩展
#import "@preview/cjk-unbreak:0.1.1": remove-cjk-break-space
// 用于自定义图表、公式的编号格式
#import "@preview/headcount:0.1.0": *
// 自定义页码
#import "@preview/numbly:0.1.0": numbly

#let 字号 = (
  初号: 42pt,
  小初: 36pt,
  一号: 26pt,
  小一: 24pt,
  二号: 22pt,
  小二: 18pt,
  三号: 16pt,
  小三: 15pt,
  四号: 14pt,
  中四: 13pt,
  小四: 12pt,
  五号: 10.5pt,
  小五: 9pt,
  六号: 7.5pt,
  小六: 6.5pt,
  七号: 5.5pt,
  小七: 5pt,
)

#let 字体 = (
  仿宋: ("Times New Roman", "FangSong"),
  宋体: ("Times New Roman", "SimSun"),
  黑体: ("Times New Roman", "SimHei"),
  楷体: ("Times New Roman", "KaiTi"),
  代码: ("Consolas", "Times New Roman", "SimSun"),
)

  // 设置参考文献样式为 GB/T 7714-2015
#let bilingual-bibliography(
  bibliography: none,
  title: "参考文献",
  full: false,
  style: "gb-7714-2015-numeric",
  mapping: (:),
  extra-comma-before-et-al-trans: false,
  // 用于控制多位译者时表现为 `et al. tran`(false) 还是 `et al., tran`(true)
  allow-comma-in-name: false,
  // 如果使用的 CSL 中，英文姓名中会出现逗号，请设置为 true
) = {
  set text(字号.五号, font: 字体.宋体)
  assert(bibliography != none, message: "请传入带有 source 的 bibliography 函数。")

  // Please fill in the remaining mapping table here
  mapping = (
    //"等": "et al",
    "卷": "Vol.",
    "册": "Bk.",
    // "译": ", tran",
    // "等译": "et al. tran",
    // 注: 请见下方译者数量判断部分。
  ) + mapping

  let to-string(content) = {
    if content.has("text") {
      content.text
    } else if content.has("children") {
      content.children.map(to-string).join("")
    } else if content.has("child") {
      to-string(content.child)
    } else if content.has("body") {
      to-string(content.body)
    } else if content == [ ] {
      " "
    }
  }

  show grid.cell.where(x: 1): it => {
    // 后续的操作是对 string 进行的。
    let ittext = to-string(it)
    // 判断是否为中文文献：去除特定词组后，仍有至少两个连续汉字。
    let pureittext = ittext.replace(regex("[等卷册和版本章期页篇译间者(不详)]"), "")
    if pureittext.find(regex("\p{sc=Hani}{2,}")) != none {
      // 新增功能：将带有"标准"两个字的一行中的 [Z] 替换为 [S]
      ittext = ittext.replace(
      regex("标准.*\[Z\]"),
      itt => {
        itt.text.replace(regex("\[Z\]"), "[S]")
      },
      )
      ittext
    } else {
      // 若不是中文文献，进行替换
      // 新增功能：将英文ISO标准的 [Z] 替换为 [S]
      ittext = ittext.replace(
      regex("ISO.*\[Z\]"),
      itt => {
        itt.text.replace(regex("\[Z\]"), "[S]")
      },
      )
      // 第xxx卷、第xxx册的情况：变为 Vol. XXX 或 Bk. XXX。
      let reptext = ittext
      reptext = reptext.replace(
      regex("(第\s?)?\d+\s?[卷册]"),
      itt => {
        if itt.text.contains("卷") {
        "Vol. "
        } else {
        "Bk. "
        }
        itt.text.find(regex("\d+"))
      },
      )

      // 第xxx版/第xxx本的情况：变为 1st ed 格式。
      reptext = reptext.replace(
        regex("(第\s?)?\d+\s?[版本]"),
        itt => {
          let num = itt.text.find(regex("\d+"))
          num
          if num.clusters().len() == 2 and num.clusters().first() == "1" {
            "th"
          } else {
            (
              "1": "st",
              "2": "nd",
              "3": "rd",
            ).at(num.clusters().last(), default: "th")
          }
          " ed"
        },
      )

      // 译者数量判断：单数时需要用 trans，复数时需要用 tran 。
      /*
      注:
          1. 目前判断译者数量的方法非常草率：有逗号就是多个作者。但是在部分 GB/T 7714-2015 方言中，姓名中可以含有逗号。如果使用的 CSL 是姓名中含有逗号的版本，请将 bilingual-bibliography 的 allow-comma-in-name 参数设为 true。
          2. 在 GB/T 7714-2015 原文中有 `等译`（P15 10.1.3 小节 示例 1-[1] 等），但未给出相应的英文缩写翻译。CSL 社区库内的 GB/T 7714-2015 会使用 `等, 译` 和 `et al., tran` 的写法。为使中英文与标准原文写法一致，本小工具会译作 `et al. tran`。若需要添加逗号，请将 bilingual-bibliography 的 extra-comma-before-et-al-trans 参数设为 true。
          3. GB/T 7714-2015 P8 7.2 小节规定：“译”前需加逗号。因此单个作者的情形，“译” 会被替换为 ", trans"。与“等”并用时的情况请见上一条注。
          如果工作不正常，可以考虑换为简单关键词替换，即注释这段情况，取消 13 行 mapping 内 `译` 条目的注释。
      */
      reptext = reptext.replace(regex("\].+?译"), itt => {
        // 我想让上面这一行匹配变成非贪婪的，但加问号后没啥效果？
        let comma-in-itt = itt.text.replace(regex(",?\s?译"), "").matches(",")
        if (
          type(comma-in-itt) == array and 
          comma-in-itt.len() >= (
              if allow-comma-in-name {2} else {1}
            )
          ) {
          if extra-comma-before-et-al-trans {
            itt.text.replace(regex(",?\s?译"), ", tran")
          } else {
            itt.text.replace(regex(",?\s?译"), " tran")
          }
        } else {
          itt.text.replace(regex(",?\s?译"), ", trans")
        }
      })

      // `等` 特殊处理：`等`后方接内容也需要译作 `et al.`，如 `等译` 需要翻译为 `et al. trans`
      reptext = reptext.replace(
        regex("等."),
        itt => {
          "et al."
          // 如果原文就是 `等.`，则仅需简单替换，不需要额外处理
          // 如果原文 `等` 后没有跟随英文标点，则需要补充一个空格
          if not itt.text.last() in (".", ",", ";", ":", "[", "]", "/", "\\", "<", ">", "?", "(", ")", " ", "\"", "'") {
            " "
          }
          // 原文有英文句号时不需要重复句号，否则需要将匹配到的最后一个字符吐回来
          if not itt.text.last() == "." {
            itt.text.last()
          }
        },
      )

      // 其他情况：直接替换
      reptext = reptext.replace(
        regex("\p{sc=Hani}+"),
        itt => {
          mapping.at(itt.text, default: itt.text)
          // 注意：若替换功能工作良好，应该不会出现 `default` 情形
        },
      )
      reptext
    }
  }

  set text(lang: "zh")
  bibliography(
    title: none,
    full: full,
    style: style,
  )
}


#let conf(
  cauthor: "张三",
  eauthor: "San Zhang",
  udc: "xxxxxx-xxx-xxxxxx-xxxx-x",
  id: "xxxxxxxxx",
  studentid: "23000xxxxx",
  cheader: "北京大学博士学位论文",
  ctitle: "北京大学学位论文 Typst 模板",
  etitle: "Typst Template for Peking University Dissertations",
  school: "某个学院",
  cfirstmajor: "某个一级学科",
  cmajor: "某个专业",
  emajor: "Some Major",
  csupervisor: "李四",
  esupervisor: "Si Li",
  date: "2026年5月10日",
  cabstract: [],
  ckeywords: (),
  eabstract: [],
  ekeywords: (),
  acknowledgments: [],
  gender: "男",
  birthdate: "2000年1月1日",
  ethnicity: "汉族",
  email: "zhangsan@cuit.edu.cn",
  doc
) = {
  // 外部包调用
  show: show-cn-fakebold // 中文伪粗体
  show: remove-cjk-break-space // 去除 CJK 换行空格

  set page(
    paper: "a4",
    margin: (bottom: 2.54cm, top: 2.54cm, left: 3.17cm, right: 3.17cm),
  )
  // 页码逻辑：封面页不显示页码，摘要、目录页罗马数字页码，正文阿拉伯数字页码
  let front-counter = counter("front-counter") // 用于标记摘要、目录页结束，初始值为 0
  set page(footer: context {
    set align(center)
    set text(字号.小五, font: 字体.宋体)
    // context[物理页码：#here().page()] // debug
    // context[front页码：#front-counter.get().at(0) | ] // debug
    if front-counter.get().at(0) == 0 {
       return
    }
    else if front-counter.get().at(0) == 10 {
      counter(page).display("I")
    }
    else { // front-counter = 20
        counter(page).display(
          numbly("{1}", "第{1}页/共{2}页"),
          both: true,
        )
    }
  })


  // 统一设置行间距，等效 word 的 1.25 倍行距
  set text(top-edge: 0.7em, bottom-edge: -0.3em)
  let linespace = 0.63em
  set par(leading: linespace, spacing: linespace)

  // 封面 Cover page
  // set page(numbering: none)
  align(center)[
    #set text(字号.小四, font: 字体.宋体)
    #box[
      #set align(left + top)
      #strong("分类号：TP311.5") #h(11em) #strong("U D C：") #strong(udc)
      #linebreak()
      #strong("密　级：公 开　") #h(11em) #strong(" 编  号：") #strong(id)
    ]
  ]

  align(center)[
    #par("") #par("") #par("") #par("")
    #set text(字号.三号, font: 字体.宋体)
  ]

  align(center)[
    #set text(字号.二号, font: 字体.黑体, tracking: 0.25cm)
    #par[
      *成都信息工程大学*
      #linebreak()
      *学位论文*
    ]
  ]

  align(center)[
    #par("") #par("")
    #set text(字号.三号, font: 字体.宋体)
    #strong(ctitle)
    #par("") #par("") #par("") #par("") #par("")
  ]

  align(center)[
    #set text(字号.小三, font: 字体.楷体)
    #set table(
      align: center + horizon, 
      stroke: (x, y) => if x == 1 { (bottom: 0.5pt) } else { none },
      inset: (x: 0em, y: 0.5em),
    )
    #table(
      columns: (6cm, 5.53cm),
      ..(
        ([*论文作者姓名：*], [*#cauthor*]),
        ([*申请学位专业：*], [*#cmajor*]),
        ([*申请学位类别：*], [*工学学士*]),
        ([*指导教师姓名（职称）：*], [*#csupervisor*]),
        ([*论文提交日期：*], [*#date*])
      )
        .map(((first, ..rest)) => (first + linebreak(justify: true), ..rest)) 
        .flatten(),
    )
  ]

  pagebreak()

  // 罗马数字页码
  counter(page).update(1) // 重置页码为 1
  counter("front-counter").update(10)

  // 中文摘要 Chinese Abstract
  align(center)[
    #show heading: it => [
      #box()[
        #set text(字号.三号, font: 字体.黑体, spacing: 12pt)
        #set par(spacing: 12pt)
        #strong(it.body)
      ]
    ]
    #heading(numbering: none, outlined: false, ctitle)
  ]
  box[
    // 摘要正文
    #set text(字号.小四, font: 字体.宋体)
    #text(font: 字体.黑体)[*摘要：*]
    #set par(first-line-indent: (amount: 2em, all: true), justify: true)
    #cabstract
    
    #linebreak()
    #set par(first-line-indent: 0em)
    #text(font: 字体.黑体)[ *关键词：* ]
    #ckeywords.join("，")
  ]

  pagebreak()
  // 英文摘要 English Abstract
  align(center)[
    #show heading: it => [
      #box()[
        #set text(字号.三号, font: 字体.黑体, spacing: 12pt)
        #set par(spacing: 12pt)
        #strong(it.body)
      ]
    ]
    #heading(numbering: none, outlined: false, etitle)
  ]
  block()[
    // 摘要正文
    #set text(字号.小四, font: 字体.宋体)
    #text(font: 字体.黑体)[*Abstract:*]
    #set par(first-line-indent: (amount: 2em, all: true), justify: true)
    #text(font: 字体.宋体)[ #eabstract ]
    
    #linebreak()
    #set par(first-line-indent: 0em)
    #text(font: 字体.黑体)[ *Key words：* ]
    #ekeywords.join("，")
  ]

  pagebreak()

  // 目录
  align(center)[
    #show heading: it => [
      #set text(字号.三号, font: 字体.宋体, spacing: 12pt)
      #set par(spacing: 12pt)
      #strong(it.body)
    ]
    #heading(numbering: none, outlined: false, "目　录")
  ]
  align(right)[
    #set text(字号.小四, font: 字体.宋体)
    论文总页数：#context[#counter(page).final().first()]
  ]
  set text(字号.小四, font: 字体.宋体)
  outline(title: none, depth: 3)

  pagebreak()

  // 设置标题样式
  set heading(numbering: "1.1.1")
  show heading.where(level: 1): it => {
    set align(center)
    set text(字号.小三, font: 字体.黑体, weight: "regular")
    set block(below: 1.5em)
    it
  }
  show heading.where(level: 2): it => {
    set text(字号.四号, font: 字体.黑体, weight: "regular")
    set block(below: 1em)
    it
  }
  show heading.where(level: 3): it => {
    set text(字号.小四, font: 字体.黑体, weight: "regular")
    set block(above: 1em)
    it
  }

  // 设置图表
  let _set_figure(body) ={

    // 设置图表标题前缀
    show figure.where(kind: image): set figure(supplement: [图])
    show figure.where(kind: table): set figure(supplement: [表])

    // 设置表标题位置为上方
    show figure.where(kind: table): set figure.caption(position: top)

    // 设置图表标题样式
    show figure.caption: set text(font: 字体.黑体, size: 字号.五号)
    set figure.caption(separator: " ") // 分隔符：标题编号与文字间空格分隔

   // 设置图表编号为分章编号格式
   set figure(numbering: dependent-numbering("1.1"))
   set math.equation(numbering: dependent-numbering("(1.1)"))
   // 保证图表/公式在每章从 1 开始编号
   show heading: reset-counter(counter(figure.where(kind: image)))
   show heading: reset-counter(counter(figure.where(kind: table)))
   show heading: reset-counter(counter(math.equation))

   // 设置允许图表跨页 
   show figure: set block(breakable: true)

    // 设置公式标题样式
    set math.equation(supplement: [公式])
    body
  }
  show: _set_figure

  // 设置表格样式为三线表
  let three-line-table = it => {
    if it.children.any(c => c.func() == table.hline) {
      return it
    }

    let toprule = table.hline(stroke: 0.08em)
    let bottomrule = toprule
    let midrule = table.hline(stroke: 0.05em)

    let meta = it.fields()
    meta.stroke = none
    meta.remove("children")

    let header = it.children.find(c => c.func() == table.header)
    let cells = it.children.filter(c => c.func() == table.cell)
    if header == none {
      let columns = meta.columns.len()
      header = table.header(..cells.slice(0, columns))
      cells = cells.slice(columns)
    }

    return table(
      ..meta,
      toprule,
      header,
      midrule,
      ..cells,
      bottomrule,
    )
  }
  show table: three-line-table
  // 设置表格单元格字体样式
  show table.cell: set text(font: 字体.宋体, size: 字号.五号)
  // 表头加粗
  show table.cell.where(y: 0): set text(weight: "bold")

  // 设置代码块样式
  show raw: set text(字号.五号, font: 字体.代码)

  // 设置正文内容样式
  set text(字号.小四, font: 字体.宋体, lang: "zh", region: "cn")
  set par(first-line-indent: (amount: 2em, all: true), justify: true)

  // 起始页码
  counter(page).update(1) // 重置页码为 1
  counter("front-counter").update(20)

  // 正文内容占位
  doc
  pagebreak()
  // 参考文献
  heading(numbering: none)[参考文献]

  bilingual-bibliography(bibliography: bibliography.with("references.bib"))

  pagebreak()
  // 致谢
  heading(numbering: none)[致 谢]
  acknowledgments
  v(4em)
  grid(
    columns: (1fr, 1fr),
    gutter: 0.8em,
    [ 作者简介： ],
    [ ],
    [姓#h(2em)名：#cauthor ],
    [性别：#gender],
    [出生年月：#birthdate],
    [民族：#ethnicity ],
    [E-mail: #email]
  )

  pagebreak()
  heading(numbering: none)[声 明]
  [
    本论文的工作是20  年  月至20  年  月在成都信息工程大学#school 完成的。
    文中除了特别加以标注地方外，不包含他人已经发表或撰写过的研究成果，
    也不包含为获得成都信息工程大学或其他教学机构的学位或证书而使用过的材料。

    关于学位论文使用权和研究成果知识产权的说明：

    本人完全了解成都信息工程大学有关保管使用学位论文的规定，其中包括：

    (1) 学校有权保管并向有关部门递交学位论文的原件与复印件。

    (2) 学校可以采用影印、缩印或其他复制方式保存学位论文。

    (3) 学校可以学术交流为目的复制、赠送和交换学位论文。

    (4) 学校可允许学位论文被查阅或借阅。

    (5) 学校可以公布学位论文的全部或部分内容（保密学位论文在解密后遵守此规定）。

    除非另有科研合同和其他法律文书的制约，本论文的科研成果属于成都信息工程大学。

    特此声明！

    #align(right)[
      作者签名：#h(2.8em)       

      #date
    ]
  ]

  // context text.font // debug
  // context text.size // debug
}
