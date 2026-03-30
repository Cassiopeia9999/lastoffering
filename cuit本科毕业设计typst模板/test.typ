#import "@preview/headcount:0.1.0": *

#let mycounter = counter("hello")

#set heading(numbering: "1.1")
// #show heading: reset-counter(mycounter, levels: 1)


= First heading

#context mycounter.step()
#context mycounter.display(dependent-numbering("1.1"))

= Second heading

#context mycounter.step()
#context mycounter.display(dependent-numbering("1.1"))

#context mycounter.step()
#context mycounter.display(dependent-numbering("1.1"))
