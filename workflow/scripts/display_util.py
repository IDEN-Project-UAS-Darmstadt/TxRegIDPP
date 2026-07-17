"""Utilities to display data, schemas and workflow info"""

from pathlib import Path
import datetime
import pandas as pd
from IPython.display import display, Markdown, HTML
from pandas.api.types import is_numeric_dtype
from yaml import load, SafeLoader, dump
from itertools import chain
import hashlib
import pandera.pandas as pa
from matplotlib import pyplot as plt
from matplotlib_venn import venn2, venn3
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.ioff()
plt.rcParams["figure.figsize"] = (8, 5)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", None)
# import networkx as nx
# from pyvis.network import Network


def collist(cols):
    if len(cols) == 0:
        return "No columns"
    seps = [", " for _ in cols]
    if len(cols) > 1:
        seps[-2] = " and "
    seps[-1] = ""
    ticked = [f"`{c}`{sep}" for c, sep in zip(cols, seps)]
    return "".join(ticked)


def sha256sum(filename: str):
    """Returns the SHA256 Digest of the given file

    Args:
        filename (str): Path to the file

    Returns:
        str: SHA256 Digest
    """
    with open(filename, "rb", buffering=0) as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def filechangedate(f: str):
    """Return the timestamp, when the file was last changed

    Args:
        f (str): Path to the file

    Returns:
        datetime: Change timestamp
    """
    return datetime.datetime.fromtimestamp(f.lstat().st_mtime)


def rule_setup(inputs, inputignored={"util", "display_util"}):
    inputfiles = {k: v for k, v in inputs.items() if Path(v).is_file()}
    params = {k: v for k, v in inputs.items() if Path(v).is_file() is False}
    fmt = "%d.%m.%Y %H:%M:%S"
    if len(params) != 0:
        display(pd.Series(params, name="Parameters").to_frame())
    display(Markdown("**Input**:"))
    ins = {
        i: [filechangedate(Path(i)).strftime(fmt), sha256sum(i)]
        for k, i in inputfiles.items()
        if k not in inputignored
    }
    changes = pd.DataFrame.from_dict(
        ins, orient="index", columns=["Last change", "Hash"]
    )
    display(changes)
    display(Markdown("**Ran at**: " + datetime.datetime.now().strftime(fmt)))


def rename(data: pd.DataFrame, renamedict: dict):
    """Create a table from a dictionary used for renaming and rename the data

    Args:
        data (pd.DataFrame): The data
        renamedict (dict): The renaming dict

    Returns:
        pd.DataFrame: Renamed data
    """
    assert sum((k in data.columns for k in renamedict)) == len(
        renamedict
    ), "Not all renaming keys present in data"
    assert sum((k in renamedict for k in data.columns)) == len(
        data.columns
    ), "Not all data columns present!"
    duplicates = pd.Series(renamedict).reset_index(drop=True)
    assert len(duplicates[duplicates.duplicated()]) == 0, "Duplicated names present!"
    # display(Markdown("The following table shows the new column names."))
    toshow = (
        pd.merge(
            data.columns.to_series().rename("names"),
            pd.Series(renamedict, name="new"),
            left_index=True,
            right_index=True,
            how="left",
        )
        .drop(columns="names")
        .rename(columns={"new": "New Name"})
    )
    toshow.index.rename("Old Name", inplace=True)
    display(toshow)
    return data.rename(columns=renamedict)


def schema_info(schema: pa.DataFrameSchema):
    """Create a data representation of the schema

    Args:
        schema (pa.DataFrameSchema): The schema

    Returns:
        dict: Dictionary with entries for the index and columns, aswell as basic info
    """
    schema = load(schema.to_yaml(), Loader=SafeLoader)

    def colstodf(cols):
        colnames = {
            "title": "Title",
            "description": "Description",
            "dtype": "Data Type",
            "nullable": "Nullable",
            "unique": "Unique",
            "checks": "Checks",
        }
        res = pd.DataFrame(cols).T[list(colnames.keys())]
        res["dtype"] = "<pre>" + res["dtype"] + "</pre>"
        ch = ~res["checks"].isna()
        res["title"] = '<span style="white-space: nowrap;">' + res["title"] + "</span>"
        res.loc[ch, "checks"] = (
            '<pre style="text-align:left;white-space: nowrap;">'
            + res.loc[ch, "checks"].apply(dump).str.replace("\n", "</br>")
            + "</pre>"
        )
        with pd.option_context("future.no_silent_downcasting", True):
            return res.rename(columns=colnames).fillna("")

    index = {ix["name"]: ix for ix in schema["index"]}
    schema["index"] = colstodf(index)
    schema["columns"] = colstodf(schema["columns"])
    return schema


def fcount(count, total):
    return f"{count} ({100*count/total:.2f} %)"


def summarize_index(data: pd.DataFrame):
    """Create a dataframe describing the index of the given data

    Args:
        data (pd.DataFrame): Each column has rows with information
    """

    def summarize_index_col(col):
        uniq = col.nunique()
        total = len(col)
        nas = col.isna().sum()
        valcounts = col.value_counts()
        res = pd.Series(
            {
                "Number of Distinct Values (Ignoring Missing Values)": fcount(
                    uniq, total
                ),
                "Number of Missing Values": fcount(nas, total),
            }
        )
        repeats = summarize_numericals(valcounts).drop(
            index=["Number of Not Missing Values"]
        )
        repeats = repeats.set_axis("Repeats " + repeats.index, axis=0)
        return pd.concat([res, repeats])

    data = data.index.to_frame().reset_index(drop=True)
    data[" + ".join(data.columns)] = data.groupby(list(data.columns)).ngroup()
    return data.agg(summarize_index_col)


def count(series):
    return fcount(series.count(), series.size)


def nunique(series):
    return fcount(series.nunique(), series.size)


def summarize_index_overlap(
    a: pd.DataFrame,
    b: pd.DataFrame,
    a_label: str,
    b_label: str,
    c: pd.DataFrame = None,
    c_label: str = None,
):
    """Compares the index of the two or three given dataframes with a table and venn diagramm"""
    summar = [summarize_index(a), summarize_index(b)]
    labels = [a_label, b_label]
    if c is not None:
        summar += [summarize_index(c)]
        labels += [c_label]
    display(pd.concat(summar, axis=1, keys=labels))

    display(
        Markdown(
            "\n\nThe following Venn-diagramm shows the overlap of the unique entries.\n\n"
        )
    )
    f, ax = plt.subplots(1, 1)
    ax.set_title("Overlap of unique entries")
    a_index = a.index.drop_duplicates()
    b_index = b.index.drop_duplicates()

    if c is None:
        a_only = a_index[~a_index.isin(b_index)]
        overlap = b_index.intersection(a_index)
        b_only = b_index[~b_index.isin(a_index)]

        all_vals = a_only.size + b_only.size + overlap.size
        _ = venn2(
            {"10": a_only.size, "01": b_only.size, "11": overlap.size},
            set_labels=labels,
            ax=ax,
            subset_label_formatter=lambda x: fcount(x, all_vals),
        )
    else:
        c_index = c.index.drop_duplicates()
        sets = (set(a_index), set(b_index), set(c_index))
        all_vals = set()
        for curset in sets:
            all_vals |= curset
        all_vals = len(all_vals)
        _ = venn3(
            sets,
            set_labels=labels,
            ax=ax,
            subset_label_formatter=lambda x: fcount(x, all_vals),
        )
    display(f)
    plt.close(f)


def summarize_categoricals(data: pd.DataFrame, official_doc: pd.DataFrame = None):
    """Treat the columns in data as categoricals and summarize them

    Args:
        data (pd.DataFrame): The data

    Returns:
        pd.DataFrame: Each column has rows with information
    """

    def info(series):
        row_info = official_doc[official_doc["Shortnames in der BED-DB"] == series.name]
        if len(row_info) == 0:
            return "NA"
        return row_info.iloc[0][
            "Beschreibung"
        ]  # es wird der erste datensatz genommen... (eigentlich sollte es nur einer sein)

    def content(series):
        row_info = official_doc[official_doc["Shortnames in der BED-DB"] == series.name]
        if len(row_info) == 0:
            return "NA"
        return row_info.iloc[0][
            "Inhalt/Form"
        ]  # es wird der erste datensatz genommen... (eigentlich sollte es nur einer sein)

    def most_common(series):
        counts = series.value_counts(dropna=True)
        if len(counts) == 0:
            return "All NA"
        return f"'{counts.index[0]}' ({counts.iloc[0]})"

    def least_common(series):
        counts = series.value_counts(dropna=True)
        if len(counts) == 0:
            return "All NA"
        return f"'{counts.index[-1]}' ({counts.iloc[-1]})"

    def list_values(series):
        max_values = 5
        unique_values = series.dropna().unique()
        if len(unique_values) > max_values:
            return f"{len(unique_values)} unique values"

        unique_values = [f'"{v}"' for v in unique_values]
        return ", ".join(unique_values)

    aggs = [count, nunique, most_common, least_common, list_values]
    human_names = [
        "Number of Not Missing Values",
        "Number of Distinct Values (Ignoring Missing Values)",
        "Most Common Value",
        "Least Common Value",
        "All distinct Values",
    ]
    if isinstance(official_doc, pd.DataFrame):
        aggs.insert(0, info)
        human_names.insert(0, "Registry Description")

        aggs.insert(1, content)
        human_names.insert(1, "Registry Title")
    res = data.agg(aggs)
    res = res.set_axis(
        human_names,
        axis=0,
    )
    return res


def summarize_numericals(data, official_docs: pd.DataFrame = None):
    """Treat the columns in data as numericals and summarize them

    Args:
        data (pd.DataFrame): The data

    Returns:
        pd.DataFrame: Each column has rows with information
    """
    describe = data.describe().set_axis(
        [
            "Number of Not Missing Values",
            "Mean Value",
            "Standard Deviation",
            "Mininum",
            "25th Percentile",
            "Median",
            "75th Percentile",
            "Maximum",
        ],
        axis=0,
    )
    if official_docs is not None:
        filtered_docs = official_docs.loc[
            official_docs["Shortnames in der BED-DB"].isin(describe.columns),
            ["Shortnames in der BED-DB", "Beschreibung", "Inhalt/Form"],
        ]

        filtered_docs = filtered_docs.rename(
            columns={
                "Inhalt/Form": "Registry Title",
                "Beschreibung": "Registry Description",
            }
        )
        filtered_docs = filtered_docs.set_index("Shortnames in der BED-DB").transpose()

        merged_df = pd.concat([filtered_docs, describe], axis=0)
        return merged_df

    return describe


def summarize_strings(data, official_doc: pd.DataFrame = None):
    """Treat the columns in data as text information and summarize them

    Args:
        data (pd.DataFrame): The data

    Returns:
        pd.DataFrame: Each column has rows with information
    """

    def multi_nominal_analysis(series):
        row_count = series.count()
        sum_of_space = series.str.contains(" ", regex=False).sum()
        sum_of_coma = series.str.contains(",", regex=False).sum()
        sum_of_semicolon = series.str.contains(";", regex=False).sum()
        delim_count = sum_of_space + sum_of_semicolon + sum_of_coma
        if delim_count / row_count >= 0.25:
            split = series.str.split(r"[ ;,]")
            alltokens = pd.Series(chain.from_iterable(split))
            alltokens = summarize_categoricals(alltokens, official_doc=None).drop(
                index=["Number of Not Missing Values"]
            )
            alltokens = alltokens.set_axis("Token " + alltokens.index, axis=0)
            return alltokens
        else:
            return []

    lens = pd.DataFrame({col: data[col].str.len() for col in data})
    lens = summarize_numericals(lens).drop(index=["Number of Not Missing Values"])
    lens = lens.set_axis("Text Length " + lens.index, axis=0)
    cats = summarize_categoricals(data, official_doc)
    # tokens = pd.DataFrame({col: token_analysis(data[col].dropna()) for col in data})#depricated
    # print({col:data for col, data in {col: nominal_analysis(data[col].dropna(), multi=False) for col in data}.items() if len(data) != 0})
    multi_nominals = pd.DataFrame(
        {
            col: data
            for col, data in {
                col: multi_nominal_analysis(data[col].dropna()) for col in data
            }.items()
            if len(data) != 0
        }
    )
    return [
        pd.concat(
            [
                cats[cats.columns.difference(multi_nominals.columns)],
                lens[lens.columns.difference(multi_nominals.columns)],
            ],
            axis=0,
        ),
        pd.concat(
            [
                cats[cats.columns.intersection(multi_nominals.columns)],
                multi_nominals,
                lens[lens.columns.intersection(multi_nominals.columns)],
            ],
            axis=0,
        ),
    ]


def classify_tokens(tokens):
    pass


def summarize(data: pd.DataFrame, limit: int, official_doc: pd.DataFrame = None):
    """Return a dictionary with summarizing information on each column

    Args:
        data (pd.DataFrame): The data
        limit (int): How many values will lead to a column to be considered not a categorical?

    Returns:
        dict: Dictionary with one key for each column data category
    """
    nuniques = data.nunique()
    numTest = data.dtypes.apply(
        lambda dtype: dtype.name == "float64" or dtype.name == "int64"
    )  # sind alle tokens zahlen?
    categoricals_sel = nuniques < limit  # categoricals_sel: weniger tokens als limit
    # single_values_sel = nuniques == 1

    new_cat_sel = (
        categoricals_sel & ~numTest
    )  # & ~units_sel #Kategorie = wenig tokens & keine zahl & keine unit

    categoricals = nuniques.index[new_cat_sel]  # & ~single_values_sel
    numerics = nuniques.index[
        ~new_cat_sel & data.apply(is_numeric_dtype)
    ]  # mehr tokens als limit und nummerisch
    strings = nuniques.index[
        ~new_cat_sel
        & data.apply(
            lambda col: col.dtype.kind == "O"
        )  # mehr tokens als limit und Datentyp = object
    ]
    # single_values = nuniques.index[
    #    single_values_sel
    # ]  # eine konstante einheit (in jeder spalte)

    assert len(numerics) + len(categoricals) + len(strings) == len(
        data.columns
    )  # + len(single_values)

    if len(categoricals) > 0:
        categoricals = summarize_categoricals(data[categoricals], official_doc)
    else:
        categoricals = None
    if len(numerics) > 0:
        numerics = summarize_numericals(data[numerics], official_doc)
    else:
        numerics = None
    if len(strings) > 0:
        strings = summarize_strings(data[strings], official_doc)
    else:
        strings = [None, None]
    return {
        "cat": categoricals,
        "numerics": numerics,
        "nominal": strings[0],
        "multi nominal": strings[1],
    }


def display_data_doc(
    schema=None, data=None, limit=20, columns_only=False, official_doc=None
):
    """Display a formatted Markdown combined information block and schema and data

    Args:
        schema (pa.DataFrameSchema): The schema
        data (pd.DataFrame): The data
        limit (int): How many values will lead to a column to be considered not a categorical?
    """
    if schema is not None:
        res = schema_info(schema)
        display(Markdown(f'**Title:** {res["title"]}'))
        display(Markdown(f'**Description:** {res["description"]}'))
        display(Markdown("Index:\n"))
        display(HTML(res["index"].to_html(escape=False)))
        display(Markdown("Columns:\n"))
        display(HTML(res["columns"].to_html(escape=False)))
        display(Markdown("Further Checks:\n\nNone"))
    if data is not None:
        sums = summarize(data, limit, official_doc)
        if not columns_only:
            display(
                Markdown(
                    f"The data has {data.shape[0]} rows and {data.shape[1]} columns."
                )
            )
        if sums["cat"] is not None and sums["cat"].shape[1] != 0:
            display(
                Markdown(
                    f'Summary statistics for the {sums["cat"].shape[1]} columns, which contained categorical data are shown in the next table. Categorical data was defined as having less than {limit} distinct values.\n'
                )
            )
            display(sums["cat"])
        if sums["numerics"] is not None and sums["numerics"].shape[1] != 0:
            display(
                Markdown(
                    f'The next table shows summary statistics for the {sums["numerics"].shape[1]} columns with numerical data. \n'
                )
            )
            display(sums["numerics"])
        if sums["nominal"] is not None and sums["nominal"].shape[1] != 0:
            display(
                Markdown(
                    f'This table shows the {sums["nominal"].shape[1]} columns which contain nominal data.\n'
                )
            )
            display(sums["nominal"])
        if sums["multi nominal"] is not None and sums["multi nominal"].shape[1] != 0:
            display(
                Markdown(
                    f'This final table shows the {sums["multi nominal"].shape[1]} columns with multi nominal data.\n'
                )
            )
            display(sums["multi nominal"])


def display_long_data_doc(data, idcols, datecol, typecol):
    data = data.copy()
    contentcols = list(data.columns)
    contentcols.remove(datecol)
    for idcol in idcols:
        contentcols.remove(idcol)
    if typecol:
        contentcols.remove(typecol)
        display(
            Markdown(
                f"""In this longitudinal data the subjects are identified by {collist(idcols)}
        at the measurement time `{datecol}`. Different measurement types are in the column `{typecol}` and these measurements
        are in {collist(contentcols)}. The following table shows the distribution of measurements across the different types.
        """
            )
        )
    else:
        display(
            Markdown(
                f"""In this longitudinal data the subjects are identified by {collist(idcols)}
        at the measurement time `{datecol}`. The measurements
        are in {collist(contentcols)}. The following table shows the distribution of measurements across.
        """
            )
        )
        assert "Test Type" not in data.columns
        data["Test Type"] = "All"
        typecol = "Test Type"
    totalrows = data.groupby(typecol).size()
    fullsplit = data.groupby(idcols + [typecol]).size()
    subjects = (fullsplit != 0).groupby(typecol).sum()
    counts = (
        fullsplit.groupby(typecol)
        .agg(["min", "mean", "max"])
        .set_axis(
            [
                "Minimum number of rows for a subject",
                "Average number of rows for a subject",
                "Maximum number of rows for a subject",
            ],
            axis=1,
        )
    )
    typesummary = pd.concat(
        [totalrows, subjects],
        keys=["Rows with this type", "Subjects with this type"],
        axis=1,
    )
    typesummary = pd.concat([typesummary, counts], axis=1)
    display(typesummary)
    display(
        Markdown(
            "In the following plots the measurement times and the difference to the next measurement time are shown."
        )
    )
    toplot = data.loc[:, [typecol, datecol] + idcols].copy()
    assert datecol != "date__min"
    toplot["date__min"] = toplot.groupby(idcols)[datecol].transform(
        lambda vals: vals - vals.min()
    )
    f, (ax1, ax2) = plt.subplots(1, 2)
    sns.ecdfplot(data=toplot, x="date__min", hue=typecol, ax=ax1)
    ax1.set_xlabel("Time since the first\nmeasurement for this subject")
    ax1.set_ylabel("ECDF P(Time<=x)")
    toplot = (
        toplot.set_index(typecol)
        .groupby([typecol] + idcols)[datecol]
        .diff()
        .abs()
        .dropna()
        + 1
    ).reset_index()
    sns.ecdfplot(data=toplot, x=datecol, hue=typecol, ax=ax2, log_scale=(True, False))
    ax2.set_xlabel("Time Difference +1 between\ntwo measurements")
    ax2.set_ylabel("")
    f.suptitle("Measurement Time Distribution")
    display(f)
    plt.close(f)
    for i, g in data.groupby(typecol):
        display(Markdown(f"**Measurement data for `{typecol} = {i}`**:"))
        display_data_doc(
            None, g.loc[:, contentcols + [datecol]].dropna(how="all", axis=1)
        )
