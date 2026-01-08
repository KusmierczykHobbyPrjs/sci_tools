

## Searching for hyperparameters 
 - [create_experiments.py](create_experiments.py): Generates scripts based on a template file and value ranges selected for placeholders.

Sample template:
```
  #!/bin/bash -l
  #SBATCH --job-name=$RAWIDENTIFIER
  #SBATCH --output=$RAWIDENTIFIER-%j.out
  #SBATCH --error=errors-%j.err

  # We can set some defaults:
  IDENTIFIER="experiment_name"
  LEARNING_RATE=1e-3
  CLS_LEARNING_RATE=1e-4

  python experiment_script.py \
   experiment.exp_name=$IDENTIFIER \
   experiment.learning_rate=$LEARNING_RATE \
   experiment.cls_learning_rate=$CLS_LEARNING_RATE 
```

Sample json config:
```
  {
    "id": "id_$FILE_$DATE",
    "predefined_configs": [
      {
        "name": "baseline",
        "LEARNING_RATE": 0.1e-5,
        "CLS_LEARNING_RATE": 1e-5
      }
    ],
    "grid_search: {
      "LEARNING_RATE": [
        1e-5,
        1e-4,
        1e-3
      ],
      "CLS_LEARNING_RATE": [
        1e-5,
      ]
    }
  }
```

## Running Jupyter Notebook from command line

This Bash script [run_notebook.sh](run_notebook.sh) serves as an automation wrapper that allows to execute a Jupyter Notebook (`.ipynb`) directly from the command line as if it were a standard Python script. The script functions by taking a notebook file path and optional arguments as input. Command-line arguments can be handled in the notebook using the standard `argparse`, but one needs to handle `sys.argv` appropriately in the notebook (e.g. differentiate between running in the notebook or from command line). For example at the top of the notebook add:

```
import sys
if "ipykernel" in sys.argv[0]:
    sys.argv = [""]
```

Implementation:
 - Checks if a valid notebook file was provided as an argument.
 - Converts the notebook to Python, filters out `run_line_magic` commands (like `%matplotlib inline`), and modifies `os.chdir` commands to `sys.path.append` to prevent unexpected directory changes.
 - Checks if the .py version already exists to avoid unnecessary re-conversion.
 - Changes the working directory (`cd`) to the notebook's location so that file operations inside the script (e.g., loading data) work correctly.
 - Runs the generated Python script with any trailing arguments (`$@`) provided by the user.

TODO: Checks if the .py version which already exists is matches the notebook (has the notebook changed?). 

## Parsing markdown (e.g. from a GPT output) into LaTeX and for Google docs
 - [gptmd2latex.py](gptmd2latex.py): takes a markdown file and produces a LaTeX file
 - [gptmd2md.py](gptmd2md.py): takes a markdown file and outputs a cleaned version of it. Use `--gdoc_math` argument to generate a variant with correctly handled math equations, which can be displayed by **VSCode** and then, copied into a **Google document**. To prevent **VSCode** from parsing math equations uncheck `Markdown > Math: Enabled` in `Settings`. Then, use **Auto-LaTeX Equations** extension to parse the same math in the **Google document**. 
 - [clean_watermarks.py](clean_watermarks.py): takes a text file and removes watermarks (e.g. special characters) left by some chatbots.
 
 
## Combine multiple Python files and shorten their docstrings

The python script [cat_python_files.py](cat_python_files.py) combine multiple Python files with shortened docstrings.
 
