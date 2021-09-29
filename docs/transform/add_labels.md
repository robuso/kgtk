## Overview

The add-labels command copies its input file to its output file,
adding label columns using values obtained from a labels file.

`kgtk add-labels` is implemented as an alias for [`kgtk lift`](lift.md).
Unlike `kgtk lift`, `kgtk add-labels` will lift labels for all columns with
names that do not end in ';label' (or the current suffix).  A seperate label
file is required; it may be specified using either `--label-file LABEL_FILE`
or the `KGTK_LABEL_FILE` envar.  The input file is assumeed to be small enough
to fit into memory, and the labels will be read with prefiltering.
Any lifted columns that are entirely empty will be suppressed.

See the `kgtk lift` documentation for more details on the shared behavior
of these two commands.

### Memory Usage

The input rows are saved in memory, as well as the value-to-label mapping.
This will impose a limit on the size of the input files that can be processed.

## Usage

```
usage: kgtk lift [-h] [-i INPUT_FILE] [-o OUTPUT_FILE]
                 [--label-file INPUT_FILE]
                 [--unmodified-row-output-file UNMODIFIED_ROW_OUTPUT_FILE]
                 [--matched-label-output-file MATCHED_LABEL_OUTPUT_FILE]
                 [--unmatched-label-output-file UNMATCHED_LABEL_OUTPUT_FILE]
                 [--columns-to-write [OUTPUT_LIFTED_COLUMN_NAMES [OUTPUT_LIFTED_COLUMN_NAMES ...]]]
                 [--default-value DEFAULT_VALUE]
                 [--suppress-empty-columns [True/False]]
                 [--ok-if-no-labels [True/False]]
                 [--prefilter-labels [True/False]]
                 [--input-file-is-presorted [True/False]]
                 [--label-file-is-presorted [True/False]]
                 [--clear-before-lift [CLEAR_BEFORE_LIFT]]
                 [--overwrite [OVERWRITE]]
                 [--output-only-modified-rows [OUTPUT_ONLY_MODIFIED_ROWS]]
                 [-v [optional True|False]]

Lift labels for a KGTK file. If called as "kgtk lift", for each of the items in the (node1, label, node2) columns, look for matching label records. If called as "kgtk add-labels", look for matching label records for all input columns. If found, lift the label values into additional columns in the current record. Label records are removed from the output unless --remove-label-records=False. 

Additional options are shown in expert help.
kgtk --expert lift --help

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        The KGTK input file. (May be omitted or '-' for
                        stdin.)
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        The KGTK output file. (May be omitted or '-' for
                        stdout.)
  --label-file INPUT_FILE
                        A KGTK file with label records (Optional, use '-' for
                        stdin.)
  --unmodified-row-output-file UNMODIFIED_ROW_OUTPUT_FILE
                        A KGTK output file that will contain only unmodified
                        rows. This file will have the same columns as the
                        input file. (Optional, use '-' for stdout.)
  --matched-label-output-file MATCHED_LABEL_OUTPUT_FILE
                        A KGTK output file that will contain matched label
                        edges. This file will have the same columns as the
                        source of the labels, either the input file or the
                        label file. (Optional, use '-' for stdout.)
  --unmatched-label-output-file UNMATCHED_LABEL_OUTPUT_FILE
                        A KGTK output file that will contain unmatched label
                        edges. This file will have the same columns as the
                        source of the labels, either the input file or the
                        label file. (Optional, use '-' for stdout.)
  --columns-to-write [OUTPUT_LIFTED_COLUMN_NAMES [OUTPUT_LIFTED_COLUMN_NAMES ...]]
                        The columns into which to store the lifted values. The
                        default is [node1;label, label;label, node2;label,
                        ...] or their aliases.
  --default-value DEFAULT_VALUE
                        The value to use if a lifted label is not found.
                        (default=)
  --suppress-empty-columns [True/False]
                        If true, do not create new columns that would be
                        empty. (default=True).
  --ok-if-no-labels [True/False]
                        If true, do not abort if no labels were found.
                        (default=False).
  --prefilter-labels [True/False]
                        If true, read the input file before reading the label
                        file. (default=True).
  --input-file-is-presorted [True/False]
                        If true, the input file is presorted on the column for
                        which values are to be lifted. (default=False).
  --label-file-is-presorted [True/False]
                        If true, the label file is presorted on the node1
                        column. (default=False).
  --clear-before-lift [CLEAR_BEFORE_LIFT]
                        If true, set columns to write to the default value
                        before lifting. (default=False).
  --overwrite [OVERWRITE]
                        If true, overwrite non-default values in the columns
                        to write. If false, do not overwrite non-default
                        values in the columns to write. (default=True).
  --output-only-modified-rows [OUTPUT_ONLY_MODIFIED_ROWS]
                        If true, output only modified edges to the primary
                        output stream. (default=False).

  -v [optional True|False], --verbose [optional True|False]
                        Print additional progress messages (default=False).
```

## Examples

### Sample Data

Suppose that `add-labels-file1.tsv` contains the following table in KGTK format:

```bash
kgtk cat --input-file examples/docs/add-labels-file1.tsv
```

| node1 | label | node2 | color |
| -- | -- | -- | -- |
| Q1 | P1 | Q5 | Q101 |
| Q1 | P2 | Q6 | Q102 |
| Q6 | P1 | Q5 | Q103 |

Suppose also that `add-labels-file2.tsv` contains the following table in KGTK format:

```bash
kgtk cat --input-file examples/docs/add-labels-file2.tsv
```

| node1 | label | node2 |
| -- | -- | -- |
| Q1 | label | "Elmo" |
| Q2 | label | "Alice" |
| Q5 | label | "human" |
| Q6 | label | "Fred" |
| P1 | label | "instance of" |
| P2 | label | "friend" |
| Q101 | label | "red" |
| Q102 | label | "blue" |
| Q103 | label | "green" |


### Adding Labels to an Input File with Extra Columns

Let's add labels to `add-labels-file1.tsv`.  This file
contains the additional column `color`.

```bash
kgtk add-labels --input-file examples/docs/add-labels-file1.tsv \
                --label-file examples/docs/add-labels-file2.tsv
```

The output will be the following table in KGTK format:

| node1 | label | node2 | color | node1;label | label;label | node2;label | color;label |
| -- | -- | -- | -- | -- | -- | -- | -- |
| Q1 | P1 | Q5 | Q101 | "Elmo" | "instance of" | "human" | "red" |
| Q1 | P2 | Q6 | Q102 | "Elmo" | "friend" | "Fred" | "blue" |
| Q6 | P1 | Q5 | Q103 | "Fred" | "instance of" | "human" | "green" |

`kgtk lift` has moved the labels into additional columns and removed
the label edges from the output file.

### Adding Labels with an Existing Label Coluymn

Suppose that `add-labels-file3.tsv` contains the following table in KGTK format:

```bash
kgtk cat --input-file examples/docs/lift-file4.tsv
```

| node1 | label | node2 |
| -- | -- | -- |
| Q1 | P1 | Q5 |
| Q1 | P2 | Q6 |
| Q1 | label | "Elmo" |
| Q2 | label | "Alice" |
| P1 | label | "instance of" |
| P2 | label | "friend" |
| P2 | label | "amigo" |
| Q5 | label | "human" |
| Q5 | label | "homo sapiens" |
| Q5 | label | "human" |
| Q6 | P1 | Q5 |
| Q6 | label | "Fred" |

Lift this file with no additional arguments:

```bash
kgtk add-labels --input-file examples/docs/add-labels-file3.tsv \
                --label-file examples/docs/add-labels-file2.tsv
```

| node1 | label | node2 | color | node1;label | label;label | node2;label | color;label |
| -- | -- | -- | -- | -- | -- | -- | -- |
| Q1 | P1 | Q5 | Q101 | "Elmo" | "instance of" | "human" | "red" |
| Q1 | P2 | Q6 | Q102 | "Elmo" | "friend" | "Fred" | "blue" |
| Q6 | P1 | Q5 | Q103 | "Fred" | "instance of" | "human" | "green" |

### Suppression of Empty Label Columns

Suppose that `add-labels-file3.tsv` contains the following table in KGTK format:

```bash
kgtk cat --input-file examples/docs/lift-file4.tsv
```

| node1 | label | node2 |
| -- | -- | -- |
| Q1 | P1 | Q5 |
| Q1 | P2 | Q6 |
| Q1 | label | "Elmo" |
| Q2 | label | "Alice" |
| P1 | label | "instance of" |
| P2 | label | "friend" |
| P2 | label | "amigo" |
| Q5 | label | "human" |
| Q5 | label | "homo sapiens" |
| Q5 | label | "human" |
| Q6 | P1 | Q5 |
| Q6 | label | "Fred" |

Lift this file, which includes the `nolabel` column, which contains
values that are not labels in the labels file:

```bash
kgtk add-labels --input-file examples/docs/add-labels-file4.tsv \
                --label-file examples/docs/add-labels-file2.tsv
```

The output will be the following table in KGTK format:

| node1 | label | node2 | color | node1;label | nolabel | label;label | node2;label | color;label |
| -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Q1 | P1 | Q5 | Q101 | "Elmo" | Q201 | "instance of" | "human" | "red" |
| Q1 | P2 | Q6 | Q102 | "Elmo" | Q202 | "friend" | "Fred" | "blue" |
| Q6 | P1 | Q5 | Q103 | "Fred" | Q203 | "instance of" | "human" | "green" |
