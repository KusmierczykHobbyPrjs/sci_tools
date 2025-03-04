

## Parsing markdown (e.g. from a GPT output) into LaTeX and for Google docs
 - [gptmd2latex.py](gptmd2latex.py): takes a markdown file and produces a LaTeX file
 - [gptmd2md.py](gptmd2md.py): takes a markdown file and outputs a cleaned version of it. Pass `--gdoc_math` argument to generate a variant, which can be displayed by VSCode and copied into a Google document. Use `Auto-LaTeX Equations` extension to parse math in the document. 