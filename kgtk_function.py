import csv
from io import StringIO
from IPython.core.display import display, HTML, JSON, Markdown
import json
import os
import pandas
import sh
import sys
import typing

def kgtk(arg1: typing.Union[str, pandas.DataFrame],
         arg2: typing.Optional[str] = None,
         df: typing.Optional[pandas.DataFrame] = None,
         auto_display_md: typing.Optional[bool] = None,
         auto_display_json: typing.Optional[bool] = None,
         auto_display_html: typing.Optional[bool] = None,
         kgtk_command: typing.Optional[str] = None,
         bash_command: typing.Optional[str] = None,
         )->typing.Optional[pandas.DataFrame]:
    """This function simplifies using KGTK commands in a Jupyter Lab environment.

    Invocation
    ==========

    kgtk("pipeline")

    Execute the command pipeline.  The results are printed, displayed, or
    returned as a Pandas DataFrame.

    kgtk(df, "pipeline")

    The `df` in the call is a Pandas DataFrame, which is converted to KGTK
    format and passed to the pipeline as standard input. The results are
    printed, displayed, or returned as a Pandas DataFrame.

    Optional Parameters
    ======== ==========

    df=DF (default None)
    
    This is an alternat method for specifying an input DataFrame.

    auto_display_md=True/False (default False)

    This parameter controls the processing of MarkDown output.  See below.

    auto_display_json=True/False (default True)

    This parameter controls the processing of JSON output.  See below.

    auto_display_html=True/False (default True)

    This parameter controls the processing of HTML output.  See below.

    kgtk_command=CMD (default 'kgtk')

    This parameter specifies the kgtk shell command.  If the envar KGTK_KGTK_COMMAND
    is present, it will supply the default value for the name of the `kgtk` command.

    One use for this feature is to redefine the `kgtk` command to include
    `time` as a prefix, and/or to include common options.

    bash_command=CMD (default 'bash')

    This parameter specifies the name of the shell interpreter.  If the envar
    KGTK_BASH_COMMAND is present, it will supply the default value for the
    name of the shell interpreter.

    Standard Output Processing
    ======== ====== =========

    If the standard output of the pipeline is MarkDown format (typically by
    ending the pipeline in `... / md` or `... /table`, identified as starting
    with `|`, the output will be printed by default.  However, if
    `auto_display_md=True` is passed in the `kgtk(...)` call, or if the envar
    `KGTK_AUTO_DISPLAY_MD` is set to `true`, then the MarkDown will be
    displayed using `display(Markdown(output))`.

    If the standard output of the pipeline is in JSON format (`--output-format JSON`),
    identified as starting with `[` or '{', the output will be displayed with
    `display(JSON(output))` by default.  However, if
    `kgtk(... auto_display_json=False)` or if the envar
    `KGTK_AUTO_DISPLAY_JSON` set to `false`, then the output will be printed.

    If the standard output of the pipeline is in HTML format (`--output-format HTML` or
    `kgtk("... /html")`), identified by starting with `<!DOCTYPE html>`, the
    output will be displayed with `display(HTML(output))` by default.
    However, if `kgtk(... auto_display_json=False)` or if the envar
    `KGTK_AUTO_DISPLAY_HTML` set to `false`, then the output will be printed.

    If the standard output starts with anything other than `|`, `[`, or `<!DOCTYPE
    html>`, then the output is assumed to be in KGTK format.  It is converted
    to a Pandas DataFrame, which is returned to the caller.

    Error Output Processing
    ===== ====== ==========

    If standard output was printed or displayed, then any error output will be printed
    immediately after it.

    If standard output was convertd to a DataFrame and returned, and
    subsequently displayed by the iPython shell, then any error output will be
    printed before the DataFrame is displayed.

    """

    # Set the defaults:
    if auto_display_md is None:
        auto_display_md = os.getenv("KGTK_AUTO_DISPLAY_MD", "false").lower() in ["true", "yes", "y"]
    if auto_display_json is None:
        auto_display_json = os.getenv("KGTK_AUTO_DISPLAY_JSON", "true").lower() in ["true", "yes", "y"]
    if auto_display_html is None:
        auto_display_html = os.getenv("KGTK_AUTO_DISPLAY_HTML", "true").lower() in ["true", "yes", "y"]
    if kgtk_command is None:
        kgtk_command = os.getenv("KGTK_KGTK_COMMAND", "kgtk")
    if bash_command is None:
        bash_command = os.getenv("KGTK_BASH_COMMAND", "bash")

    MD_SIGIL: str = "|"
    JSON_SIGIL: str = "["
    JSONL_MAP_SIGIL: str = "{"
    HTML_SIGIL: str = "<!DOCTYPE html>"
    USAGE_SIGIL: str = "usage:"

    in_df: typing.Optional[pandas.DataFrame] = None
    pipeline: str
    if isinstance(arg1, str):
        if arg2 is not None:
            raise ValueError("kgtk(arg1, arg2): arg2 is not allowed when arg1 is a string")
        pipeline = arg1
    elif isinstance(arg1, pandas.DataFrame):
        if arg2 is None:
            raise ValueError("kgtk(arg1, arg2): arg2 is required when arg1 is a DataFrame")
        in_df = arg1
        pipeline = arg2

    if df is not None:
        if in_df is not Nont:
            raise ValueError("kgtk(): df= is not allowed when arg1 is a DataFrame")

    if len(pipeline) == 0:
        raise ValueError("kgtk(...): the pipeline is empty")
    pipeline = kgtk_command + " " + pipeline

    in_tsv: typing.Optional[str] = None
    if in_df is not None:
        in_tsv = in_df.to_csv(sep='\t',
                              index=False,
                              quoting=csv.QUOTE_NONNUMERIC,
                              quotechar='"',
                              doublequote=False,
                              escapechar='\\',
                              )

    outbuf: StringIO = StringIO()
    errbuf: StringIO = StringIO()

    sh_bash = sh.Command(bash_command)
    sh_bash("-c", pipeline, _in=in_tsv, _out=outbuf, _err=errbuf)

    output: str = outbuf.getvalue()

    # Decide what to do based on the start of the output:
    result: typing.Optional[pandas.DataFrame] = None
    if output.startswith(MD_SIGIL):
        if auto_display_md:
            display(Markdown(output))
        else:
            print(output)

    elif output.startswith(JSON_SIGIL) or output.startswith(JSONL_MAP_SIGIL):
        if auto_display_json:
            display(JSON(json.loads(output)))
        else:
            print(output)

    elif output[:len(HTML_SIGIL)].lower() == HTML_SIGIL.lower():
        if auto_display_html:
            display(HTML(output))
        else:
            print(output)

    elif output.startswith(USAGE_SIGIL):
        print(output)

    else:
        # result = pandas.read_csv(StringIO(output), sep='\t')
        outbuf.seek(0)
        result = pandas.read_csv(outbuf, sep='\t')

    outbuf.close()

    # Any error messages? If so, print the at the end.
    errout: str = errbuf.getvalue()
    if len(errout) > 0:
        print(errout)

    return result
