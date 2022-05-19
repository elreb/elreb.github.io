# Data Science Interview Prep Guide

Data Science interviews are tough, this guide has notes and example questions and solutions to go over various topics that you may be asked during a Data Science interview.

### To [build the bookdown document](https://bookdown.org/yihui/bookdown/build-the-book.html):
* *html* - `bookdown::render_book("index.Rmd", "bookdown::gitbook")`
* *pdf* - `bookdown::render_book("index.Rmd", "bookdown::pdf_book")`

### Troubleshooting:

**Knitting md file issues**

1. If some text after a code block is converting to a code block remove the line breaks and [use 4 spaces as an indent for sub-items](https://stackoverflow.com/questions/18088955/markdown-continue-numbered-list)

![Bad code](assets/images/text_as_code_chunk.png?raw=true "Bad code - notice orange color")
![Bad code output](assets/images/text_as_code_chunk_2.png?raw=true "Bad code - result")
![Good code](assets/images/text_as_code_chunk_3.png?raw=true "Good code - notice text appropriate white color")

