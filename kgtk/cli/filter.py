"""
Filter rows by subject, predicate, object values.
"""
from argparse import Namespace, SUPPRESS
import typing

from kgtk.cli_argparse import KGTKArgumentParser, KGTKFiles

def parser():
    return {
        'help': 'Filter rows by subject, predicate, object values.',
        'description': 'Filter KGTK file based on values in the node1 (subject), ' +
        'label (predicate), and node2 (object) fields.  Optionally filter based on ' +
        'regular expressions.'
    }


def add_arguments_extended(parser: KGTKArgumentParser, parsed_shared_args: Namespace):
    """
    Parse arguments
    Args:
        parser (argparse.ArgumentParser)
    """
    from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
    from kgtk.utils.argparsehelpers import optional_bool
    from kgtk.value.kgtkvalueoptions import KgtkValueOptions

    _expert: bool = parsed_shared_args._expert

    # '$label == "/r/DefinedAs" && $node2=="/c/en/number_zero"'
    parser.add_input_file(positional=True)
    parser.add_output_file(who="The KGTK output file for records that pass the filter. Multiple output file may be specified, each with their own pattern.", allow_list=True, dest="output_files")
    parser.add_output_file(who="The KGTK reject file for records that fail the filter.",
                           dest="reject_file",
                           options=["--reject-file"],
                           metavar="REJECT_FILE",
                           optional=True)

    # parser.add_argument('-dt', "--datatype", action="store", type=str, dest="datatype", help="Datatype of the input file, e.g., tsv or csv.", default="tsv")
    parser.add_argument('-p', '--pattern', action="append", nargs="+", type=str, dest="patterns", required=True,
                        help="Pattern to filter on, for instance, \" ; P154 ; \". Multiple patterns may be specified when there are mutiple output files.")
    parser.add_argument('--subj', action="store", type=str, dest='subj_col', help="Subject column, default is node1")
    parser.add_argument('--pred', action="store", type=str, dest='pred_col', help="Predicate column, default is label")
    parser.add_argument('--obj', action="store", type=str, dest='obj_col', help="Object column, default is node2")

    parser.add_argument(      "--or", dest="or_pattern", metavar="True|False",
                              help="'Or' the clauses of the pattern. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    parser.add_argument(      "--invert", dest="invert", metavar="True|False",
                              help="Invert the result of applying the pattern. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    parser.add_argument(      "--regex", dest="regex", metavar="True|False",
                              help="When True, treat the filter clauses as regular expressions. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    parser.add_argument(      "--first-match-only", dest="first_match_only", metavar="True|False",
                              help="If true, write only to the file with the first matching pattern.  If false, write to all files with matching patterns. (default=%(default)s).",
                              type=optional_bool, nargs='?', const=True, default=False)

    parser.add_argument(      "--show-version", dest="show_version", type=optional_bool, nargs='?', const=True, default=False,
                              help="Print the version of this program. (default=%(default)s).", metavar="True/False")

    KgtkReader.add_debug_arguments(parser, expert=_expert)
    KgtkReaderOptions.add_arguments(parser, mode_options=True, expert=_expert)
    KgtkValueOptions.add_arguments(parser, expert=_expert)

def run(input_file: KGTKFiles,
        output_files: KGTKFiles,
        reject_file: KGTKFiles,

        patterns: typing.List[typing.List[str]],
        subj_col: typing.Optional[str],
        pred_col: typing.Optional[str],
        obj_col: typing.Optional[str],

        or_pattern: bool,
        invert: bool,
        regex: bool,
        first_match_only: bool,

        show_version: bool,

        errors_to_stdout: bool = False,
        errors_to_stderr: bool = True,
        show_options: bool = False,
        verbose: bool = False,
        very_verbose: bool = False,

        **kwargs # Whatever KgtkFileOptions and KgtkValueOptions want.
)->int:
    # import modules locally
    from pathlib import Path
    import re
    import sys
    
    from kgtk.exceptions import kgtk_exception_auto_handler, KGTKException
    from kgtk.io.kgtkreader import KgtkReader, KgtkReaderOptions
    from kgtk.io.kgtkwriter import KgtkWriter
    from kgtk.value.kgtkvalueoptions import KgtkValueOptions

    input_kgtk_file: Path = KGTKArgumentParser.get_input_file(input_file)
    output_kgtk_files: typing.List[Path] = KGTKArgumentParser.get_output_file_list(output_files, default_stdout=True)
    reject_kgtk_file: typing.Optional[Path] = KGTKArgumentParser.get_optional_output_file(reject_file, who="KGTK reject file")

    # Select where to send error messages, defaulting to stderr.
    error_file: typing.TextIO = sys.stdout if errors_to_stdout else sys.stderr

    # Build the option structures.
    reader_options: KgtkReaderOptions = KgtkReaderOptions.from_dict(kwargs)
    value_options: KgtkValueOptions = KgtkValueOptions.from_dict(kwargs)

    UPDATE_VERSION: str = "2020-11-07T00:06:18.672326+00:00#pITaI1X5E06A9vDdSeUUZObybGWrp0gh86XOFGM431y3KmQ7Gbg6OngTWFLLuBaA4HLhSEVol+XZZIF1LkXf/Q=="
    if show_version or verbose:
        print("kgtk filter version: %s" % UPDATE_VERSION, file=error_file, flush=True)

    # Show the final option structures for debugging and documentation.
    if show_options:
        print("--input-file=%s" % str(input_kgtk_file), file=error_file)
        print("--output-file=%s" % " ".join([str(x) for x in output_kgtk_files]), file=error_file)
        if reject_kgtk_file is not None:
            print("--reject-file=%s" % str(reject_kgtk_file), file=error_file)
        print("--pattern=%s" % " ".join(repr(patterns)), file=error_file)
        if subj_col is not None:
            print("--subj=%s" % str(subj_col), file=error_file)
        if pred_col is not None:
            print("--pred=%s" % str(pred_col), file=error_file)
        if obj_col is not None:
            print("--obj=%s" % str(obj_col), file=error_file)
        print("--or=%s" % str(or_pattern), file=error_file)
        print("--invert=%s" % str(invert), file=error_file)
        print("--regex=%s" % str(regex), file=error_file)
        print("--first-match-only=%s" % str(first_match_only), file=error_file)
        reader_options.show(out=error_file)
        value_options.show(out=error_file)
        print("=======", file=error_file, flush=True)

    def prepare_filter(pattern: str)->typing.Set[str]:
        filt: typing.Set[str] = set()
        pattern = pattern.strip()
        if len(pattern) == 0:
            return filt

        target: str
        for target in pattern.split(","):
            target=target.strip()
            if len(target) > 0:
                filt.add(target)

        return filt

    def prepare_regex(pattern: str)->typing.Optional[typing.Pattern]:
        pattern = pattern.strip()
        if len(pattern) == 0:
            return None
        else:
            return re.compile(pattern)

    def single_subject_filter(kr: KgtkReader,
                              kw: KgtkWriter,
                              rw: typing.Optional[KgtkWriter],
                              subj_idx: int,
                              subj_filter: typing.Set[str],
                              ):
        if verbose:
            print("Applying a single subject filter", file=error_file, flush=True)

        subj_filter_value: str = list(subj_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[subj_idx] == subj_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_subject_filter_inverted(kr: KgtkReader,
                                       kw: KgtkWriter,
                                       rw: typing.Optional[KgtkWriter],
                                       subj_idx: int,
                                       subj_filter: typing.Set[str],
                                       ):
        if verbose:
            print("Applying a single subject filter inverted", file=error_file, flush=True)

        subj_filter_value: str = list(subj_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[subj_idx] != subj_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_predicate_filter(kr: KgtkReader,
                                kw: KgtkWriter,
                                rw: typing.Optional[KgtkWriter],
                                pred_idx: int,
                                pred_filter: typing.Set[str],
                                ):
        if verbose:
            print("Applying a single predicate filter", file=error_file, flush=True)

        pred_filter_value: str = list(pred_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[pred_idx] == pred_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_predicate_filter_inverted(kr: KgtkReader,
                                         kw: KgtkWriter,
                                         rw: typing.Optional[KgtkWriter],
                                         pred_idx: int,
                                         pred_filter: typing.Set[str],
                                         ):
        if verbose:
            print("Applying a single predicate filter inverted", file=error_file, flush=True)

        pred_filter_value: str = list(pred_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[pred_idx] != pred_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_object_filter(kr: KgtkReader,
                             kw: KgtkWriter,
                             rw: typing.Optional[KgtkWriter],
                             obj_idx: int,
                             obj_filter: typing.Set[str],
                             ):
        if verbose:
            print("Applying a single object filter", file=error_file, flush=True)

        obj_filter_value: str = list(obj_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[obj_idx] == obj_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_object_filter_inverted(kr: KgtkReader,
                                      kw: KgtkWriter,
                                      rw: typing.Optional[KgtkWriter],
                                      obj_idx: int,
                                      obj_filter: typing.Set[str],
                                      ):
        if verbose:
            print("Applying a single object filter inverted", file=error_file, flush=True)

        obj_filter_value: str = list(obj_filter)[0]

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            if row[obj_idx] != obj_filter_value:
                kw.write(row)
                output_line_count += 1

            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def single_general_filter(kr: KgtkReader,
                              kw: KgtkWriter,
                              rw: typing.Optional[KgtkWriter],
                              subj_idx: int,
                              subj_filter: typing.Set[str],
                              pred_idx: int,
                              pred_filter: typing.Set[str],
                              obj_idx: int,
                              obj_filter: typing.Set[str]):
        if verbose:
            print("Applying a single general filter", file=error_file, flush=True)

        apply_subj_filter: bool = len(subj_filter) > 0
        apply_pred_filter: bool = len(pred_filter) > 0
        apply_obj_filter: bool = len(obj_filter) > 0

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0
        subj_filter_keep_count: int = 0
        pred_filter_keep_count: int = 0
        obj_filter_keep_count: int = 0
        subj_filter_reject_count: int = 0
        pred_filter_reject_count: int = 0
        obj_filter_reject_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            keep: bool = False
            reject: bool = False 
            if apply_subj_filter:
                if row[subj_idx] in subj_filter:
                    keep = True
                    subj_filter_keep_count += 1
                else:
                    reject = True
                    subj_filter_reject_count += 1

            if apply_pred_filter:
                if row[pred_idx] in pred_filter:
                    keep = True
                    pred_filter_keep_count += 1
                else:
                    reject = True
                    pred_filter_reject_count += 1

            if apply_obj_filter:
                if row[obj_idx] in obj_filter:
                    keep = True
                    obj_filter_keep_count += 1
                else:
                    reject = True
                    obj_filter_reject_count += 1

            if (keep if or_pattern else not reject) ^ invert:
                kw.write(row)
                output_line_count += 1
            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))
            print("Keep counts: subject=%d, predicate=%d, object=%d." % (subj_filter_keep_count, pred_filter_keep_count, obj_filter_keep_count))
            print("Reject counts: subject=%d, predicate=%d, object=%d." % (subj_filter_reject_count, pred_filter_reject_count, obj_filter_reject_count))

    def dispatch_subject_filter(kr: KgtkReader,
                                kws: typing.List[KgtkWriter],
                                rw: typing.Optional[KgtkWriter],
                                subj_idx: int,
                                subj_filters: typing.List[typing.Set[str]]):
        if verbose:
            print("Applying a dispatched multiple-output subject filter", file=error_file, flush=True)

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        dispatch: typing.MutableMapping[str, KgtkWriter] = { }
        idx: int
        kw: KgtkWriter
        for idx, kw in enumerate(kws):
            subj_filter: typing.Set[str] = subj_filters[idx]
            keyword: str
            for keyword in subj_filter:
                dispatch[keyword] = kw

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            kwo: typing.Optional[KgtkWriter] = dispatch.get(row[subj_idx])
            if kwo is not None:
                kwo.write(row)
                output_line_count += 1
            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def dispatch_predicate_filter(kr: KgtkReader,
                                  kws: typing.List[KgtkWriter],
                                  rw: typing.Optional[KgtkWriter],
                                  pred_idx: int,
                                  pred_filters: typing.List[typing.Set[str]]):
        if verbose:
            print("Applying a dispatched multiple-output predicate filter", file=error_file, flush=True)

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        dispatch: typing.MutableMapping[str, KgtkWriter] = { }
        idx: int
        kw: KgtkWriter
        for idx, kw in enumerate(kws):
            pred_filter: typing.Set[str] = pred_filters[idx]
            keyword: str
            for keyword in pred_filter:
                dispatch[keyword] = kw

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            kwo: typing.Optional[KgtkWriter] = dispatch.get(row[pred_idx])
            if kwo is not None:
                kwo.write(row)
                output_line_count += 1
            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def dispatch_object_filter(kr: KgtkReader,
                               kws: typing.List[KgtkWriter],
                               rw: typing.Optional[KgtkWriter],
                               obj_idx: int,
                               obj_filters: typing.List[typing.Set[str]]):
        if verbose:
            print("Applying a dispatched multiple-output object filter", file=error_file, flush=True)

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0

        dispatch: typing.MutableMapping[str, KgtkWriter] = { }
        idx: int
        kw: KgtkWriter
        for idx, kw in enumerate(kws):
            obj_filter: typing.Set[str] = obj_filters[idx]
            keyword: str
            for keyword in obj_filter:
                dispatch[keyword] = kw

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            kwo: typing.Optional[KgtkWriter] = dispatch.get(row[obj_idx])
            if kwo is not None:
                kwo.write(row)
                output_line_count += 1
            else:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))

    def multiple_general_filter(kr: KgtkReader,
                                kws: typing.List[KgtkWriter],
                                rw: typing.Optional[KgtkWriter],
                                subj_idx: int,
                                subj_filters: typing.List[typing.Set[str]],
                                pred_idx: int,
                                pred_filters: typing.List[typing.Set[str]],
                                obj_idx: int,
                                obj_filters: typing.List[typing.Set[str]]):
        if verbose:
            print("Applying a multiple-output general filter", file=error_file, flush=True)

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0
        subj_filter_keep_count: int = 0
        pred_filter_keep_count: int = 0
        obj_filter_keep_count: int = 0
        subj_filter_reject_count: int = 0
        pred_filter_reject_count: int = 0
        obj_filter_reject_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            written: bool = False

            idx: int = 0
            for kw in kws:
                subj_filter: typing.Set[str] = subj_filters[idx]
                pred_filter: typing.Set[str] = pred_filters[idx]
                obj_filter: typing.Set[str] = obj_filters[idx]
                idx += 1
                

                keep: bool = False
                reject: bool = False 
                if len(subj_filter) > 0:
                    if row[subj_idx] in subj_filter:
                        keep = True
                        subj_filter_keep_count += 1
                    else:
                        reject = True
                        subj_filter_reject_count += 1

                if len(pred_filter) > 0:
                    if row[pred_idx] in pred_filter:
                        keep = True
                        pred_filter_keep_count += 1
                    else:
                        reject = True
                        pred_filter_reject_count += 1

                if len(obj_filter) > 0:
                    if row[obj_idx] in obj_filter:
                        keep = True
                        obj_filter_keep_count += 1
                    else:
                        reject = True
                        obj_filter_reject_count += 1

                if (keep if or_pattern else not reject) ^ invert:
                    kw.write(row)
                    if not written:
                        output_line_count += 1 # Count this only once.
                        written = True
                        if first_match_only:
                            break
                    
            if not written:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))
            print("Keep counts: subject=%d, predicate=%d, object=%d." % (subj_filter_keep_count, pred_filter_keep_count, obj_filter_keep_count))
            print("Reject counts: subject=%d, predicate=%d, object=%d." % (subj_filter_reject_count, pred_filter_reject_count, obj_filter_reject_count))

    def process_plain()->int:

        subj_filters: typing.List[typing.Set[str]] = [ ]
        pred_filters: typing.List[typing.Set[str]] = [ ]
        obj_filters: typing.List[typing.Set[str]] = [ ]

        subj_filter: typing.Set[str]
        pred_filter: typing.Set[str]
        obj_filter: typing.Set[str]


        nfilters: int = 0
        pattern_list: typing.List[str]
        pattern: str
        for pattern_list in patterns:
            for pattern in pattern_list:
                subpatterns: typing.List[str] = pattern.split(";")
                if len(subpatterns) != 3:
                    print("Error: The pattern must have three sections separated by semicolons (two semicolons total).", file=error_file, flush=True)
                    raise KGTKException("Bad pattern")
            
                subj_filter = prepare_filter(subpatterns[0])
                pred_filter = prepare_filter(subpatterns[1])
                obj_filter = prepare_filter(subpatterns[2])

                if len(subj_filter) == 0 and len(pred_filter) == 0 and len(obj_filter) == 0:
                    if verbose:
                        print("Warning: the filter %s is empty." % repr(pattern), file=error_file, flush=True)
                else:
                    subj_filters.append(subj_filter)
                    pred_filters.append(pred_filter)
                    obj_filters.append(obj_filter)
                    nfilters += 1

        if nfilters == 0:
            raise KGTKException("No filters found.")

        if nfilters != len(output_kgtk_files):
            if verbose:
                print("output files: %s" % " ".join([str(x) for x in output_kgtk_files]))
            raise KGTKException("There were %d filters and %d output files." % (nfilters, len(output_kgtk_files)))

        if verbose:
            print("Opening the input file: %s" % str(input_kgtk_file), file=error_file, flush=True)
        kr: KgtkReader = KgtkReader.open(input_kgtk_file,
                                         options=reader_options,
                                         value_options = value_options,
                                         error_file=error_file,
                                         verbose=verbose,
                                         very_verbose=very_verbose,
        )

        subj_idx: int = kr.get_node1_column_index(subj_col)
        pred_idx: int = kr.get_label_column_index(pred_col)
        obj_idx: int = kr.get_node2_column_index(obj_col)

        # Complain about a missing column only when it is needed by the pattern.
        trouble: bool = False
        if subj_idx < 0 and len(set.union(*subj_filters)) > 0:
            trouble = True
            print("Error: Cannot find the subject column '%s'." % kr.get_node1_canonical_name(subj_col), file=error_file, flush=True)
        if pred_idx < 0 and len(set.union(*pred_filters)) > 0:
            trouble = True
            print("Error: Cannot find the predicate column '%s'." % kr.get_label_canonical_name(pred_col), file=error_file, flush=True)
        if obj_idx < 0 and len(set.union(*obj_filters)) > 0:
            trouble = True
            print("Error: Cannot find the object column '%s'." % kr.get_node2_canonical_name(obj_col), file=error_file, flush=True)
        if trouble:
            # Clean up:
            kr.close()
            raise KGTKException("Missing columns.")

        kw: KgtkWriter
        kws: typing.List[KgtkWriter] = [ ]
        output_kgtk_file: Path
        for output_kgtk_file in output_kgtk_files:
            if verbose:
                print("Opening the output file: %s" % str(output_kgtk_file), file=error_file, flush=True)
            kw = KgtkWriter.open(kr.column_names,
                                 output_kgtk_file,
                                 mode=KgtkWriter.Mode[kr.mode.name],
                                 use_mgzip=reader_options.use_mgzip, # Hack!
                                 mgzip_threads=reader_options.mgzip_threads, # Hack!
                                 verbose=verbose,
                                 very_verbose=very_verbose)
            kws.append(kw)

        rw: typing.Optional[KgtkWriter] = None
        if reject_kgtk_file is not None:
            if verbose:
                print("Opening the reject file: %s" % str(reject_kgtk_file), file=error_file, flush=True)
            rw = KgtkWriter.open(kr.column_names,
                                 reject_kgtk_file,
                                 mode=KgtkWriter.Mode[kr.mode.name],
                                 use_mgzip=reader_options.use_mgzip, # Hack!
                                 mgzip_threads=reader_options.mgzip_threads, # Hack!
                                 verbose=verbose,
                                 very_verbose=very_verbose)

        if nfilters == 1:
            subj_filter = subj_filters[0]
            pred_filter = pred_filters[0]
            obj_filter = obj_filters[0]
            kw = kws[0]
            
            if len(subj_filter) == 1 and len(pred_filter) == 0 and len(obj_filter) == 0:
                if invert:
                    single_subject_filter_inverted(kr, kw, rw, subj_idx, subj_filter)
                else:
                    single_subject_filter(kr, kw, rw, subj_idx, subj_filter)

            elif len(subj_filter) == 0 and len(pred_filter) == 1 and len(obj_filter) == 0:
                if invert:
                    single_predicate_filter_inverted(kr, kw, rw, pred_idx, pred_filter)
                else:
                    single_predicate_filter(kr, kw, rw, pred_idx, pred_filter)

            elif len(subj_filter) == 0 and len(pred_filter) == 0 and len(obj_filter) == 1:
                if invert:
                    single_object_filter_inverted(kr, kw, rw, obj_idx, obj_filter)
                else:
                    single_object_filter(kr, kw, rw, obj_idx, obj_filter)
            else:
                single_general_filter(kr, kw, rw, subj_idx, subj_filter, pred_idx, pred_filter, obj_idx, obj_filter)

        else:
            n_subj_filters: int = 0
            n_pred_filters: int = 0
            n_obj_filters: int = 0
            fidx: int
            for fidx in range(nfilters):
                n_subj_filters += len(subj_filters[fidx])
                n_pred_filters += len(pred_filters[fidx])
                n_obj_filters += len(obj_filters[fidx])
                
            if n_subj_filters> 0 and n_pred_filters == 0 and n_obj_filters == 0 and first_match_only and not invert:
                dispatch_subject_filter(kr, kws, rw, subj_idx, subj_filters)

            elif n_subj_filters == 0 and n_pred_filters > 0 and n_obj_filters == 0 and first_match_only and not invert:
                dispatch_predicate_filter(kr, kws, rw, pred_idx, pred_filters)

            elif n_subj_filters == 0 and n_pred_filters == 0 and n_obj_filters > 0 and first_match_only and not invert:
                dispatch_object_filter(kr, kws, rw, obj_idx, obj_filters)
                
            else:
                multiple_general_filter(kr, kws, rw, subj_idx, subj_filters, pred_idx, pred_filters, obj_idx, obj_filters)

        for kw in kws:
            kw.close()
        if rw is not None:
            rw.close()

        return 0

    def multiple_general_regex(kr: KgtkReader,
                                kws: typing.List[KgtkWriter],
                                rw: typing.Optional[KgtkWriter],
                                subj_idx: int,
                                subj_filters: typing.List[typing.Optional[typing.Pattern]],
                                pred_idx: int,
                                pred_filters: typing.List[typing.Optional[typing.Pattern]],
                                obj_idx: int,
                                obj_filters: typing.List[typing.Optional[typing.Pattern]]):
        if verbose:
            print("Applying a multiple-output general regex filter", file=error_file, flush=True)

        input_line_count: int = 0
        reject_line_count: int = 0
        output_line_count: int = 0
        subj_filter_keep_count: int = 0
        pred_filter_keep_count: int = 0
        obj_filter_keep_count: int = 0
        subj_filter_reject_count: int = 0
        pred_filter_reject_count: int = 0
        obj_filter_reject_count: int = 0

        row: typing.List[str]
        for row in kr:
            input_line_count += 1

            written: bool = False

            idx: int = 0
            for kw in kws:
                subj_filter: typing.Optional[typing.Pattern] = subj_filters[idx]
                pred_filter: typing.Optional[typing.Pattern] = pred_filters[idx]
                obj_filter: typing.Optional[typing.Pattern] = obj_filters[idx]
                idx += 1
                

                keep: bool = False
                reject: bool = False 
                if subj_filter is not None:
                    subj_match: typing.Optional[typing.Match] = subj_filter.match(row[subj_idx])
                    if subj_match is not None:
                        keep = True
                        subj_filter_keep_count += 1
                    else:
                        reject = True
                        subj_filter_reject_count += 1

                if pred_filter is not None:
                    pred_match: typing.Optional[typing.Match] = pred_filter.match(row[pred_idx])
                    if pred_match is not None:
                        keep = True
                        pred_filter_keep_count += 1
                    else:
                        reject = True
                        pred_filter_reject_count += 1

                if obj_filter is not None:
                    obj_match: typing.Optional[typing.Match] = obj_filter.match(row[obj_idx])
                    if obj_match is not None:
                        keep = True
                        obj_filter_keep_count += 1
                    else:
                        reject = True
                        obj_filter_reject_count += 1

                if (keep if or_pattern else not reject) ^ invert:
                    kw.write(row)
                    if not written:
                        output_line_count += 1 # Count this only once.
                        written = True
                        if first_match_only:
                            break
                    
            if not written:
                if rw is not None:
                    rw.write(row)
                reject_line_count += 1

        if verbose:
            print("Read %d rows, rejected %d rows, wrote %d rows." % (input_line_count, reject_line_count, output_line_count))
            print("Keep counts: subject=%d, predicate=%d, object=%d." % (subj_filter_keep_count, pred_filter_keep_count, obj_filter_keep_count))
            print("Reject counts: subject=%d, predicate=%d, object=%d." % (subj_filter_reject_count, pred_filter_reject_count, obj_filter_reject_count))

    def process_regex()->int:
        subj_regexes: typing.List[typing.Optional[typing.Pattern]] = [ ]
        pred_regexes: typing.List[typing.Optional[typing.Pattern]] = [ ]
        obj_regexes: typing.List[typing.Optional[typing.Pattern]] = [ ]

        subj_regex: typing.Optional[typing.Pattern]
        pred_regex: typing.Optional[typing.Pattern]
        obj_regex: typing.Optional[typing.Pattern]

        subj_needed: bool = False
        pred_needed: bool = False
        obj_needed: bool = False

        nfilters: int = 0
        pattern_list: typing.List[str]
        pattern: str
        for pattern_list in patterns:
            for pattern in pattern_list:
                subpatterns: typing.List[str] = pattern.split(";")
                if len(subpatterns) != 3:
                    print("Error: The pattern must have three sections separated by semicolons (two semicolons total).", file=error_file, flush=True)
                    raise KGTKException("Bad pattern")
            
                subj_regex = prepare_regex(subpatterns[0])
                pred_regex = prepare_regex(subpatterns[1])
                obj_regex = prepare_regex(subpatterns[2])

                if subj_regex is None and pred_regex is None and obj_regex is None:
                    if verbose:
                        print("Warning: the filter %s is empty." % repr(pattern), file=error_file, flush=True)
                else:
                    subj_regexes.append(subj_regex)
                    pred_regexes.append(pred_regex)
                    obj_regexes.append(obj_regex)
                    nfilters += 1

                    if subj_regex is not None:
                        subj_needed = True
                    if pred_regex is not None:
                        pred_needed = True
                    if obj_regex is not None:
                        obj_needed = True

        if nfilters == 0:
            raise KGTKException("No filters found.")

        if nfilters != len(output_kgtk_files):
            if verbose:
                print("output files: %s" % " ".join([str(x) for x in output_kgtk_files]))
            raise KGTKException("There were %d filters and %d output files." % (nfilters, len(output_kgtk_files)))

        if verbose:
            print("Opening the input file: %s" % str(input_kgtk_file), file=error_file, flush=True)
        kr: KgtkReader = KgtkReader.open(input_kgtk_file,
                                         options=reader_options,
                                         value_options = value_options,
                                         error_file=error_file,
                                         verbose=verbose,
                                         very_verbose=very_verbose,
        )

        subj_idx: int = kr.get_node1_column_index(subj_col)
        pred_idx: int = kr.get_label_column_index(pred_col)
        obj_idx: int = kr.get_node2_column_index(obj_col)

        # Complain about a missing column only when it is needed by the pattern.
        trouble: bool = False
        if subj_idx < 0 and subj_needed:
            trouble = True
            print("Error: Cannot find the subject column '%s'." % kr.get_node1_canonical_name(subj_col), file=error_file, flush=True)
        if pred_idx < 0 and pred_needed > 0:
            trouble = True
            print("Error: Cannot find the predicate column '%s'." % kr.get_label_canonical_name(pred_col), file=error_file, flush=True)
        if obj_idx < 0 and obj_needed > 0:
            trouble = True
            print("Error: Cannot find the object column '%s'." % kr.get_node2_canonical_name(obj_col), file=error_file, flush=True)
        if trouble:
            # Clean up:
            kr.close()
            raise KGTKException("Missing columns.")

        kw: KgtkWriter
        kws: typing.List[KgtkWriter] = [ ]
        output_kgtk_file: Path
        for output_kgtk_file in output_kgtk_files:
            if verbose:
                print("Opening the output file: %s" % str(output_kgtk_file), file=error_file, flush=True)
            kw = KgtkWriter.open(kr.column_names,
                                 output_kgtk_file,
                                 mode=KgtkWriter.Mode[kr.mode.name],
                                 use_mgzip=reader_options.use_mgzip, # Hack!
                                 mgzip_threads=reader_options.mgzip_threads, # Hack!
                                 verbose=verbose,
                                 very_verbose=very_verbose)
            kws.append(kw)

        rw: typing.Optional[KgtkWriter] = None
        if reject_kgtk_file is not None:
            if verbose:
                print("Opening the reject file: %s" % str(reject_kgtk_file), file=error_file, flush=True)
            rw = KgtkWriter.open(kr.column_names,
                                 reject_kgtk_file,
                                 mode=KgtkWriter.Mode[kr.mode.name],
                                 use_mgzip=reader_options.use_mgzip, # Hack!
                                 mgzip_threads=reader_options.mgzip_threads, # Hack!
                                 verbose=verbose,
                                 very_verbose=very_verbose)

        multiple_general_regex(kr, kws, rw, subj_idx, subj_regexes, pred_idx, pred_regexes, obj_idx, obj_regexes)

        for kw in kws:
            kw.close()
        if rw is not None:
            rw.close()

        return 0

    try:
        if regex:
            return process_regex()
        else:
            return process_plain()

    except Exception as e:
        kgtk_exception_auto_handler(e)
        return 1
