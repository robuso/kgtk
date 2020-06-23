"""
Reorder KGTK file columns (while copying)

TODO: Need KgtkWriterOptions
"""

from argparse import Namespace, SUPPRESS
from pathlib import Path
import typing

from kgtk.cli_argparse import KGTKArgumentParser

def parser():
    return {
        'help': 'Reorder KGTK file columns.',
        'description': 'This command reorders one or more columns in a KGTK file. ' +
        '\n\nReorder all columns using --columns col1 col2' +
        '\nReorder selected columns using --columns col1 col2 ... ' +
        '\n\nThe input filename must come before --columns. ' +
        '\nIf no input filename is provided, the default is to read standard input. ' +
        '\n\nAdditional options are shown in expert help.\nkgtk --expert rename_columns --help'
    }


def add_arguments_extended(parser: KGTKArgumentParser, parsed_shared_args: Namespace):
    """
    Parse arguments
    Args:
        parser (argparse.ArgumentParser)
    """
    # import modules locally
    from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
    from kgtk.value.kgtkvalueoptions import KgtkValueOptions

    _expert: bool = parsed_shared_args._expert

    # This helper function makes it easy to suppress options from
    # The help message.  The options are still there, and initialize
    # what they need to initialize.
    def h(msg: str)->str:
        if _expert:
            return msg
        else:
            return SUPPRESS

    parser.add_argument(      "input_kgtk_file",
                              help="The KGTK input file. (default=%(default)s).",
                              type=Path, default="-")

    parser.add_argument("-o", "--output-file", dest="output_kgtk_file", help="The KGTK file to write (default=%(default)s).", type=Path, default="-")
    parser.add_argument(      "--output-format", dest="output_format", help=h("The file format (default=kgtk)"), type=str)

    parser.add_argument('-c', "--columns", dest="column_names", required=True, nargs='+',
                              metavar="COLUMN_NAME",
                              help="The list of reordered column names, optionally containing '...' for column names not explicitly mentioned.")

    KgtkReader.add_debug_arguments(parser, expert=_expert)
    KgtkReaderOptions.add_arguments(parser, mode_options=True, expert=_expert)
    KgtkValueOptions.add_arguments(parser, expert=_expert)

def run(input_kgtk_file: Path,
        output_kgtk_file: Path,
        output_format: typing.Optional[str],

        column_names: typing.List[str],

        errors_to_stdout: bool = False,
        errors_to_stderr: bool = True,
        show_options: bool = False,
        verbose: bool = False,
        very_verbose: bool = False,

        **kwargs # Whatever KgtkFileOptions and KgtkValueOptions want.
)->int:
    # import modules locally
    import sys
    from kgtk.exceptions import KGTKException
    from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
    from kgtk.io.kgtkwriter import KgtkWriter
    from kgtk.value.kgtkvalueoptions import KgtkValueOptions


    # Select where to send error messages, defaulting to stderr.
    error_file: typing.TextIO = sys.stdout if errors_to_stdout else sys.stderr

    # Build the option structures.
    reader_options: KgtkReaderOptions = KgtkReaderOptions.from_dict(kwargs)
    value_options: KgtkValueOptions = KgtkValueOptions.from_dict(kwargs)

    # Show the final option structures for debugging and documentation.
    if show_options:
        print("input: %s" % str(input_kgtk_file), file=error_file, flush=True)
        print("--output-file=%s" % str(output_kgtk_file), file=error_file, flush=True)
        if output_format is not None:
            print("--output-format=%s" % output_format, file=error_file, flush=True)
        print("--columns %s" % " ".join(column_names), file=error_file, flush=True)
        reader_options.show(out=error_file)
        value_options.show(out=error_file)
        print("=======", file=error_file, flush=True)

    try:

        if verbose:
            print("Opening the input file %s" % str(input_kgtk_file), file=error_file, flush=True)
        kr = KgtkReader.open(input_kgtk_file,
                             options=reader_options,
                             value_options = value_options,
                             error_file=error_file,
                             verbose=verbose,
                             very_verbose=very_verbose,
        )

        remaining_names: typing.List[str] = kr.column_names.copy()
        reordered_names: typing.List[str] = [ ]
        save_reordered_names: typing.Optional[typing.List[str]] = None

        ellipses: str = "..."

        column_name: str
        for column_name in column_names:
            if column_name == ellipses:
                if save_reordered_names is not None:
                    raise KGTKException("Elipses may appear only once")
                save_reordered_names = reordered_names
                reordered_names = [ ]
            else:
                if column_name not in kr.column_names:
                    raise KGTKException("Unknown column name '%s'." % column_name)
                if column_name not in remaining_names:
                    raise KGTKException("Column name '%s' was duplicated in the list." % column_name)
                reordered_names.append(column_name)
                remaining_names.remove(column_name)

        if len(remaining_names) > 0 and save_reordered_names is None:
            # There are remaining column names and the ellipses was not seen.
            raise KGTKException("No ellipses, and the following columns not accounted for: %s" % " ".join(remaining_names))
        if save_reordered_names is not None:
            if len(remaining_names) > 0:
                save_reordered_names.extend(remaining_names)
            if len(reordered_names) > 0:
                save_reordered_names.extend(reordered_names)
            reordered_names = save_reordered_names

        if verbose:
            print("Opening the output file %s" % str(output_kgtk_file), file=error_file, flush=True)
        kw: KgtkWriter = KgtkWriter.open(reordered_names,
                                         output_kgtk_file,
                                         require_all_columns=True,
                                         prohibit_extra_columns=True,
                                         fill_missing_columns=False,
                                         gzip_in_parallel=False,
                                         mode=KgtkWriter.Mode[kr.mode.name],
                                         output_format=output_format,
                                         verbose=verbose,
                                         very_verbose=very_verbose,
        )

        shuffle_list: typing.List = kw.build_shuffle_list(kr.column_names)

        input_data_lines: int = 0
        row: typing.List[str]
        for row in kr:
            input_data_lines += 1
            kw.write(row, shuffle_list=shuffle_list)

        # Flush the output file so far:
        kw.flush()

        if verbose:
            print("Read %d data lines from file %s" % (input_data_lines, input_kgtk_file))

        kw.close()

        return 0

    except SystemExit as e:
        raise KGTKException("Exit requested")
    except Exception as e:
        raise KGTKException(str(e))

