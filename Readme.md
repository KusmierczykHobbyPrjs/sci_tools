

## Parsing markdown (e.g. from a GPT output) into LaTeX and for Google docs
 - [gptmd2latex.py](gptmd2latex.py): takes a markdown file and produces a LaTeX file
 - [gptmd2md.py](gptmd2md.py): takes a markdown file and outputs a cleaned version of it. Use `--gdoc_math` argument to generate a variant with correctly handled math equations, which can be displayed by **VSCode** and then, copied into a **Google document**. To prevent **VSCode** from parsing math equations uncheck `Markdown > Math: Enabled` in `Settings`. Then, use **Auto-LaTeX Equations** extension to parse the same math in the **Google document**. 