#import "template.typ": conf

// 中文摘要
#let cabstract = [
  摘要是对论文内容不加注释和评论的简短陈述，
  要求扼要说明研究工作的目的、主要方法、研究结果、结论、科学意义或应用价值等，
  是一篇具有独立性和完整性的短文。
  摘要中不宜使用公式、图表以及非公知公用的符号和术语，不标注引用文献编号。
]
#let eabstract = [
  #lorem(100)
]

#let acknowledgments = [
  毕业设计（论文）致谢中不得书写与毕业设计（论文）工作无关的人和事，
  对指导老师的致谢要实事求是。

  对其他在本研究工作中提出建议和给予帮助的老师和同学，
  应在论文中做明确的说明并表示谢意。

  这部分内容不可省略。
]

#show: doc => conf(
  cauthor: "张三",
  ctitle: "毕业设计论文题目",
  etitle: "English Title of the Thesis",
  school: "人工智能学院",
  cmajor: "人工智能",
  csupervisor: "尹庆（讲师）",
  date: "2026年5月10日",
  cabstract: cabstract,
  // 关键词不要写专业名称“人工智能”，不要写研究方向如“计算机视觉”
  ckeywords: ("Typst", "模板", "目标检测"),
  eabstract: eabstract,
  ekeywords: ("Typst", "Template", "Object Detection"),
  gender: "男",
  birthdate: "2000年1月1日",
  ethnicity: "汉族",
  email: "zhangsan@cuit.edu.cn",
  acknowledgments: acknowledgments,
  doc
)

= 引言

== 课题背景

// 注意这里不要放国内外研究现状的内容，放在下一节
随着人工智能技术的迅猛发展，
智能辅助教学系统在教育领域的应用日益广泛，
成为推动教育现代化的重要力量， ...

== 国内外研究现状

国内外学者开展了大量相关研究，...
通过 typst 的语法进行参考文献引用非常方便，
通过调用`references.bib` 中的文献条目，即可实现自动编号、自动格式化，
文末也会自动生成参考文献列表。注意保证文献来源的真实性。

示例：
xxx 等人提出了基于深度学习的智能教学系统框架，
实现了个性化学习资源推荐与智能评测功能 @einstein1905。
参考文献引用可以连续引用多个，如示例：
近年来，随着大数据与云计算技术的发展，
智能辅助教学系统逐渐向云端迁移，
实现了更高的可扩展性与灵活性 @dirac1928 @zhang2019 @li2020。


== 研究意义

#lorem(50)

// 章节结束需要换页
#pagebreak()

= 核心技术与算法原理

// 注意这里不是重复写国内外研究现状
// 而是介绍本课题涉及的核心概念、核心算法等的简介

== 预处理算法

采用图像增强技术对输入图像进行预处理...

== 目标检测算法

目标检测是计算机视觉领域的一个重要任务，
旨在...
本课题拟采用优选的 xx 模型作为目标检测的核心算法。
该模型的主要网络架构包括...

=== 图表

正文中的图、表、公式一律采用阿拉伯数字分章编号。
如@sample-img 就是指本论文第1章的第1个图。

#figure(
  caption: [示例图片],
  image("imgs/sample-img.svg")
)<sample-img> // 需要给每个图一个唯一的标签，方便正文中使用@<标签名>引用

=== 图表文字说明

图片附近要有一段相关说明文字，解释图片内容。
如@fig:example 所示，
#lorem(30)

#figure(
  caption: [如果该图是引用自参考文献，需要在图题末尾注明出处 @einstein1905],
  image("imgs/sample-img.svg")
) <fig:example>


表格附近也要有一段相关说明文字，解释表格内容。
不同方法的性能对比如@tbl:comparison 所示，#lorem(30)

#figure(
table(
  columns: (auto, auto, auto),
  table.header(
    [方法], [准确率], [召回率],
  ),
  [方法 A], [95%], [92%],
  [方法 B], [97%], [95%],
  [方法 C], [96%], [94%],
),
caption: [不同方法的性能对比]
)<tbl:comparison>

公式附近也要有一段相关说明文字，解释公式内容及第一次出现的符号含义。
如@eq:maxwell 所示，*公式需要使用`$`符号包裹，可以借助AI助手快速生成复杂公式，
如提示词：将提供的公式图片转换为 Typst 公式代码。*
#lorem(30)
$ nabla dot bold(E) = rho / epsilon_0 $ <eq:maxwell>


#pagebreak()

= 需求分析

#lorem(50)

图片附近要有一段相关说明文字，解释图片内容。
如@fig:model 所示，
#lorem(30)

#figure(
  caption: [新章节图重新编号],
  image("imgs/sample-img.svg")
) <fig:model>

另外一个公式示例，如@eq:einstein 所示，
#lorem(30)
$ E = m c^2 $ <eq:einstein>


#pagebreak()

= 系统设计

#lorem(50)

#pagebreak()

= 系统实现

#lorem(50)

*不要大段代码堆在正文中，可以放一些关键代码片段，并且要给出代码说明文字。*
*比如使用代码片段、图片和文字说明结合的方式介绍系统模块的实现。*

比如，某个模块的关键代码如下所示，
该模块通过...实现了...功能，#lorem(20)。
最终展示效果如@fig:module-output 所示。

```python
def example_function(param1, param2):
    result = param1 + param2
    return result
```

#figure(
  caption: [模块输出示例],
  image("imgs/sample-img.svg")
) <fig:module-output>




#pagebreak()

= 系统测试与运行结果

#lorem(50)

#pagebreak()

// -----------------------------------------------------------------------------
#heading(numbering: none)[结 论]

简洁明了地总结全文的工作和主要成果，实事求是，不要夸大其词。
*根据本科论文的一般工作量，结论部分不会超过一页*。
可以指出目前存在的不足之处，并对今后的工作提出展望。
#lorem(50)

