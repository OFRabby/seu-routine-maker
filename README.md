
````markdown
# SEU Routine Maker

A Python script that converts your Southeast University (SEU) UMS class schedule into a clean, formatted PDF routine.

## Features
- Parses schedule copied from UMS (Advised Sections → Overview)
- Extracts courses, times, days, and room info
- Converts 24-hour time to 12-hour format
- Highlights labs and formats neatly in a weekly PDF (Friday to Thursday)

## Requirements
- Python 3.x
- `reportlab` library

Install dependencies:
```bash
pip install reportlab
````

## Usage

1. Run the script:

```bash
python seu_routine_maker.py
```

2. Paste your schedule text from UMS, then press Enter on an empty line.
3. Choose the folder to save your PDF or press Enter to use the current folder.
4. Find your routine as `seu_routine.pdf`.

## Author

MD. Omar Faruk Rabby

