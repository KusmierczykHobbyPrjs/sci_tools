

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

## Parsing markdown (e.g. from a GPT output) into LaTeX and for Google docs
 - [gptmd2latex.py](gptmd2latex.py): takes a markdown file and produces a LaTeX file
 - [gptmd2md.py](gptmd2md.py): takes a markdown file and outputs a cleaned version of it. Use `--gdoc_math` argument to generate a variant with correctly handled math equations, which can be displayed by **VSCode** and then, copied into a **Google document**. To prevent **VSCode** from parsing math equations uncheck `Markdown > Math: Enabled` in `Settings`. Then, use **Auto-LaTeX Equations** extension to parse the same math in the **Google document**. 
 - [clean_watermarks.py](clean_watermarks.py): takes a text file and removes watermarks (e.g. special characters) left by some chatbots.
 
