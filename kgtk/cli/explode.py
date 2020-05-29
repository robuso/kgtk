"""Copy records from the first KGTK file to the output file,
expanding | lists.

TODO: Need KgtkWriterOptions
"""

from argparse import Namespace, SUPPRESS
from pathlib import Path
import sys
import typing

from kgtk.cli_argparse import KGTKArgumentParser
from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
from kgtk.io.kgtkwriter import KgtkWriter
from kgtk.reshape.kgtkexplode import KgtkExplode
from kgtk.utils.argparsehelpers import optional_bool
from kgtk.value.kgtkvalue import KgtkValueFields
from kgtk.value.kgtkvalueoptions import KgtkValueOptions

def parser():
    return {
        'aliases': ['denormalize_node2'],
        'help': 'Copy a KGTK file, exploding one column (usualy node2) into seperate columns for each subfield.',
        'description': 'Copy a KGTK file, exploding one column (usually node2) into seperate columns for each subfield. ' +
        'If a cell in the column being exploded contains a list, that record is optionally expanded into multiple records ' +
        'before explosion, with all other columns copied-as is.' +
        '\n\nAdditional options are shown in expert help.\nkgtk --expert expand --help'
    }


def add_arguments_extended(parser: KGTKArgumentParser, parsed_shared_args: Namespace):
    """
    Parse arguments
    Args:
        parser (argparse.ArgumentParser)
    """

    _expert: bool = parsed_shared_args._expert

    parser.add_argument(      "input_kgtk_file", nargs="?", type=Path, default="-",
                              help="The KGTK file to filter. May be omitted or '-' for stdin (default=%(default)s).")

    parser.add_argument("-o", "--output-file", dest="output_kgtk_file", help="The KGTK file to write (default=%(default)s).", type=Path, default="-")

    parser.add_argument(      "--column", dest="column_name", help="The name of the column to explode. (default=%(default)s).", default="node2")

    if _expert:
        parser.add_argument(      "--fields", dest="field_names", help="The names of the fields to extract. (default=%(default)s).", nargs='+',
                                  default=KgtkValueFields.DEFAULT_FIELD_NAMES, choices=KgtkValueFields.FIELD_NAMES)
    else:
        parser.add_argument(      "--fields", dest="field_names", help="The names of the fields to extract. (default=%(default)s).", nargs='+',
                                  default=KgtkValueFields.DEFAULT_FIELD_NAMES, choices=KgtkValueFields.DEFAULT_FIELD_NAMES)
    
    parser.add_argument(      "--prefix", dest="prefix", help="The prefix for exploded column names. (default=%(default)s).", default="node2;")

    parser.add_argument(      "--overwrite", dest="overwrite_columns",
                              help="Indicate that it is OK to overwrite existing columns. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    parser.add_argument(      "--expand", dest="expand_list",
                              help="Expand the source column if it contains a list, else fail. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    KgtkReader.add_debug_arguments(parser, expert=_expert)
    KgtkReaderOptions.add_arguments(parser, mode_options=True, expert=_expert)
    KgtkValueOptions.add_arguments(parser, expert=_expert)

def run(input_kgtk_file: typing.Optional[Path],
        output_kgtk_file: typing.Optional[Path],
        column_name: str,
        field_names: typing.List[str],
        prefix: str,
        overwrite_columns: bool,
        expand_list: bool,
        
        errors_to_stdout: bool = False,
        errors_to_stderr: bool = True,
        show_options: bool = False,
        verbose: bool = False,
        very_verbose: bool = False,

        **kwargs # Whatever KgtkFileOptions and KgtkValueOptions want.
)->int:
    # import modules locally
    from kgtk.exceptions import KGTKException

    # Select where to send error messages, defaulting to stderr.
    error_file: typing.TextIO = sys.stdout if errors_to_stdout else sys.stderr

    # Build the option structures.
    reader_options: KgtkReaderOptions = KgtkReaderOptions.from_dict(kwargs)
    value_options: KgtkValueOptions = KgtkValueOptions.from_dict(kwargs)

    # Show the final option structures for debugging and documentation.
    if show_options:
        print("input: %s" % (str(input_kgtk_file) if input_kgtk_file is not None else "-"), file=error_file)
        print("--column %s" % column_name, file=error_file, flush=True)
        print("--prefix %s" % prefix, file=error_file, flush=True)
        print("--overwrite %s" % str(overwrite_columns), file=error_file, flush=True)
        print("--expand %s" % str(expand_list), file=error_file, flush=True)
        if field_names is not None:
            print("--fields %s" % " ".join(field_names), file=error_file, flush=True)
        print("--output-file=%s" % (str(output_kgtk_file) if output_kgtk_file is not None else "-"), file=error_file)
        reader_options.show(out=error_file)
        value_options.show(out=error_file)
        print("=======", file=error_file, flush=True)

    try:
        ex: KgtkExplode = KgtkExplode(
            input_file_path=input_kgtk_file,
            output_file_path=output_kgtk_file,
            column_name=column_name,
            field_names=field_names,
            prefix=prefix,
            overwrite_columns=overwrite_columns,
            expand_list=expand_list,
            reader_options=reader_options,
            value_options=value_options,
            error_file=error_file,
            verbose=verbose,
            very_verbose=very_verbose,
        )
        
        ex.process()

        return 0

    except SystemExit as e:
        raise KGTKException("Exit requested")
    except Exception as e:
        raise KGTKException(str(e))

