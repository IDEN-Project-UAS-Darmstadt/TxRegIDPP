import pandas as pd
from IPython.display import display, Markdown, HTML
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import pandera.pandas as pa
from pandera.typing import Index, String
from display_util import summarize_numericals, summarize_categoricals, fcount, collist
import warnings

sns.set_theme(style="whitegrid")
plt.ioff()
plt.rcParams["figure.figsize"] = (8, 5)
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
# from evidently import ColumnMapping
# import pandera.extensions as extensions


def replace_single_val_inplace(df, cols, val=999, newval=np.nan):
    replaced = {}
    for col in cols:
        replaceme = df[col] == val
        replaced[col] = replaceme.sum()
        df[col] = df[col].mask(replaceme, newval)
    display(
        pd.Series(
            {f"`{k}`": fcount(v, df.shape[0]) for k, v in replaced.items()},
            name=f"Replaced '{val}' times:",
        ).to_frame()
    )


def drop_col_few_distinct(df: pd.DataFrame, mindistinct: int = 1, verbose: bool = True):
    """Removes column with less than X distinct values

    Args:
        df (pd.DataFrame): The data
        mindistinct (int, optional): Minimum number of distincts. Defaults to 1.
        verbose (bool, optional): Output Markdown formatted info on the process. Defaults to True.

    Returns:
        pd.DataFrame: The data without the columns
    """
    drop = df.columns[df.nunique() < mindistinct]
    if len(drop) == 0:
        if verbose:
            display(
                Markdown(f"No columns had less than {mindistinct} distinct value(s).")
            )
        return df
    if verbose:
        display(
            Markdown(
                f"Removed {len(drop)} of {df.shape[1]} columns for not containing at least {mindistinct} distinct value(s). Dropped column(s): {collist(drop)}"
            )
        )
    return df.drop(columns=drop)


def duplicate_columns(frame):
    groups = frame.columns.to_series().groupby(frame.dtypes).groups
    dups = []
    for colnames in groups.values():
        cols = colnames.to_list()
        cols.reverse()
        for i, col1 in enumerate(cols):
            for col2 in cols[i + 1 : :]:  # noqa: E203
                if frame[col1].equals(frame[col2]):
                    dups.append(col1)
                    break
    return dups


def drop_duplicate_columns(df):
    drop = duplicate_columns(df)
    if len(drop) == 0:
        display(Markdown("No columns were duplicated."))
        return df
    display(
        Markdown(
            f"Removed {len(drop)} of {df.shape[1]} columns for being duplicates. Dropped column(s): {collist(drop)}"
        )
    )
    return df.drop(columns=drop)


# Either returns the counts of the not na column combinations or a df a selector
def notna_combinations(df, columns, return_idcombs=False):
    notna = (~df[columns].isna()).reset_index(drop=True).astype("category")
    if return_idcombs:
        return notna
    counts = (
        notna.groupby(notna.columns.to_list(), observed=False)
        .size()
        .sort_values(ascending=False)
    )
    counts = counts[counts != 0].copy()
    i = counts.index.to_frame()
    newindex = i.apply(lambda row: " + ".join(i.columns[row]), axis=1)
    newindex[newindex == ""] = np.nan
    counts = counts.rename("Number of rows with this combination").to_frame()
    counts = counts.set_axis(newindex, copy=False)
    return counts


# mindistinct: minimum number of unique values to be kept, (NA does not count)
def split_data(data, idcols, return_summar=False):
    idcols = pd.Series(idcols)
    summar = notna_combinations(data, idcols)
    groups = notna_combinations(data, idcols, True)
    indices = groups.groupby(groups.columns.to_list(), observed=False).indices
    split = {
        " + ".join(idcols[list(k)]): drop_col_few_distinct(
            data.iloc[v, :], 1, False
        ).set_index(idcols[list(k)].to_list())
        for k, v in indices.items()
    }
    cols = {k: v.columns for k, v in split.items()}
    subdata_summar = pd.DataFrame(
        {
            k: pd.Series(
                {
                    "Number of columns with data for rows with this ID combination": len(
                        v
                    )
                }
            )
            for k, v in cols.items()
        }
    ).T
    summar = pd.concat([subdata_summar, summar], axis=1)
    if return_summar:
        return summar
    display(summar)
    return split


def fix_units(df, valuecol, unitcol, targetunit, factors):
    display(Markdown(f"""All values in the column `{valuecol}` were converted
            to the unit {targetunit} based on the unit specified in
            `{unitcol}`. The following conversions happened:"""))
    assert np.isin(
        df[unitcol].dropna().unique(), [targetunit] + list(factors.keys())
    ).all(), "Some units are missing their conversion factor!"

    toshow = df[unitcol].value_counts().rename("Occurence count")
    factorstoshow = pd.Series(factors, name="Conversion factor")
    factorstoshow[targetunit] = 1
    toshow = pd.merge(
        factorstoshow, toshow, left_index=True, right_index=True, how="left"
    ).fillna(0)
    display(toshow)

    for unit, multiplicator in factors.items():
        sel = df[unitcol] == unit
        df.loc[sel, valuecol] = df.loc[sel, valuecol] * multiplicator
        df.loc[sel, unitcol] = targetunit


def common_translate(data, translation):
    translation = dict((s.split("=", 1) for s in translation))
    results = []
    data = data.stack()
    for toreplace, replacement in translation.items():
        sel = data == toreplace
        data[sel] = replacement
        cols = sel.index.get_level_values(-1)[sel].drop_duplicates()
        cols = ", ".join(cols)
        results += [
            pd.Series(
                {
                    "Replaced": toreplace,
                    "Replaced with": replacement,
                    "Replaced Count": sel.sum(),
                    "In Columns": cols,
                }
            )
        ]
    todisplay = pd.concat(results, axis=1).T.set_index("Replaced")
    todisplay = todisplay[todisplay["Replaced Count"] > 0]
    if todisplay.shape[0] > 0:
        display(todisplay)
    else:
        display(Markdown("No common translations were necessary."))
    return data.unstack().infer_objects()


def validclip(data, valid_ranges, column_mapping):
    results = []

    molten = data.loc[:, list(column_mapping.keys())].melt().dropna()
    molten["type"] = molten["variable"].replace(column_mapping)
    grouped = molten.groupby("type").indices
    for group, ix in grouped.items():
        maxval = valid_ranges[group].get("max", None)
        minval = valid_ranges[group].get("min", None)
        toplot = molten.iloc[ix, :]
        f, ax = plt.subplots(
            1, 1, figsize=(6.4, 0.5 * toplot["variable"].nunique() + 1)
        )
        sns.boxplot(data=toplot, x="value", y="variable", ax=ax)
        ax.set(xlabel=group, ylabel="Column", title=group)
        if minval is not None:
            ax.axvline(x=minval, color="orange")
        if maxval is not None:
            ax.axvline(x=maxval, color="orange")
        display(f)
        plt.close(f)

    for column, validtype in column_mapping.items():
        maxval = valid_ranges[validtype].get("max", np.Infinity)
        minval = valid_ranges[validtype].get("min", -np.Infinity)

        toobig = data.loc[:, column] > maxval
        toosmall = data.loc[:, column] <= minval
        totals = (~toosmall.isna()).sum()

        # TODO NA setting at the moment, different actions maybe in the future
        data.loc[toobig, column] = np.nan
        data.loc[toosmall, column] = np.nan

        results += [
            pd.Series(
                {
                    "Column": column,
                    "Type": validtype,
                    ">": minval,
                    "<=": maxval,
                    "Too big": fcount(toobig.sum(), totals),
                    "Too small": fcount(toosmall.sum(), totals),
                }
            )
        ]

    results = pd.concat(results, axis=1).T.set_index("Column")
    return results


# Collapses columns using an aggregate function
def collapse_col(dfslice, fun, fill=None):
    def helper(row):
        notnas = ~row.isna()
        if sum(notnas) == 0:
            return fill
        return fun(row[notnas])

    return dfslice.apply(helper, axis=1)


# Get a dict of the redundant columns
def find_redundant_cols(df, endregex=r"^(.+)_(et|dso|iqtig|\d+)$"):
    cols = df.columns.to_series()
    multis = cols.str.extract(endregex).dropna(axis=0, how="all")
    multis = (
        multis.groupby(0)
        .apply(lambda rows: rows.index.to_list(), include_groups=False)
        .to_dict()
    )
    multis = {newname: cols for newname, cols in multis.items() if len(cols) > 1}
    return multis


def fix_redundancies(data, red_cols, order=["et", "dso", "iqtig"]):  # noqa
    for newcolumn, columns in red_cols.items():
        dfslice = data.loc[:, columns]
        display(
            Markdown(
                f"The column `{newcolumn}` is redundant in {collist(columns)}. Those column have values in the following combinations:"
            )
        )
        display(
            notna_combinations(data, list(columns)).rename(
                {np.nan: "No value available"}
            )
        )
        uniques = dfslice.dtypes.drop_duplicates()
        # assert newcolumn not in data.columns This check should not have been necessary?
        assert len(uniques) == 1, "There are different dtypes!"
        presentinrow = (~dfslice.isna()).sum(axis=1)
        nomismatches = (presentinrow < 2).all()
        if nomismatches:
            display(
                Markdown(
                    "Because there is no overlap based on rows between the columns, they are combined into a single column."
                )
            )
            newval = collapse_col(dfslice, fun=lambda row: row.iloc[0])
        elif dfslice.dtypes.iloc[0].kind == "O":
            display(
                Markdown(
                    "The next table compares the general summary data of the columns."
                )
            )
            display(summarize_categoricals(dfslice, False))
            display(
                Markdown(
                    "They all contain text data, the following table lists the 10 most common combinations."
                )
            )
            combinations = (
                dfslice.groupby(dfslice.columns.to_list(), dropna=False)
                .size()
                .sort_values(ascending=False)
                .head(10)
            )
            combinations = combinations.set_axis(
                combinations.index.to_frame()
                .apply(lambda vals: ", ".join(map(str, vals)), axis=1)
                .reset_index(drop=True)
                .rename(", ".join(combinations.index.names)),
                axis=0,
            )
            combinations = combinations.rename("Occurence").to_frame()
            display(combinations)
        else:
            display(
                Markdown(
                    "The next table compares the general summary data of the columns."
                )
            )
            display(summarize_numericals(dfslice))
            display(
                Markdown("In the next plot boxplots based on each column are shown.")
            )
            f1, ax1 = plt.subplots(1, 1)
            sns.boxplot(data=dfslice.melt().dropna(), x="value", y="variable", ax=ax1)
            f1.suptitle("Distribution of the redundant columns")
            ax1.set(xlabel=newcolumn, ylabel="Redundant Columns")
            display(f1)
            plt.close(f1)
        if not nomismatches:
            cols = dfslice.columns
            regex = "^(.+)_(" + "|".join(order) + ")$"
            insts = cols.to_series().str.extract(regex).loc[:, 1]
            unmatched_cols = insts[insts.isna()].index.tolist()
            assert (
                insts.notna().all()
            ), f"Not all columns could be matched to an institution. Unmatched columns: {unmatched_cols}"
            assert insts.isin(order).all(), "Not all institutions are in the order"
            ordered_cols = list(
                sorted(
                    dfslice.columns,
                    key=lambda x: order.index(insts[cols == x].values[0]),
                )
            )
            insts = [inst for inst in order if inst in insts.values]
            dfslice = dfslice.loc[:, ordered_cols]
            newval = dfslice.iloc[:, 0]
            nasfilled = []
            for i in range(1, dfslice.shape[1]):
                nasbefore = newval.isna().sum()
                newval = newval.fillna(dfslice.iloc[:, i])
                nasafter = newval.isna().sum()
                nasfilled.append(nasbefore - nasafter)
            mainsource = f"`{insts[0].upper()}`"
            furthersources = dict(zip([f"`{g.upper()}`" for g in insts[1:]], nasfilled))
            furthersources = ", ".join(
                [f"{k} ({v} times)" for k, v in furthersources.items()]
            )
            display(
                Markdown(
                    f"The main source of data is from {mainsource}. Additional data was filled from the following sources: {furthersources}."
                )
            )
        data.drop(columns=columns, inplace=True)
        data[newcolumn] = newval
        display(HTML("\n<hr>\n"))


# https://pandera.readthedocs.io/en/stable/reference/generated/pandera.api.checks.Check.html#pandera.api.checks.Check


class EmpfaengerID(pa.DataFrameModel):
    recipient_et_id_et: Index[String] = pa.Field(
        coerce=True,
        nullable=False,
        unique=False,
        title="Organ recipient ET id",
        description="ET recipient identifier",
        str_endswith="==",
    )

    class Config:
        multiindex_strict = True
        multiindex_coerce = True


class SpenderID(pa.DataFrameModel):
    donor_et_id_et: Index[String] = pa.Field(
        coerce=True,
        nullable=True,
        unique=False,
        title="Organ donor ET id",
        description="ET donor identifier sourced from the ET contributed rows to the transplantation file.",
        str_endswith="==",
    )

    class Config:
        multiindex_strict = True
        multiindex_coerce = True


class TransplantPostOPID(pa.DataFrameModel):
    transplant_et_id: Index[String] = pa.Field(
        coerce=True,
        nullable=True,
        unique=False,
        title="Transplant ET id",
        description="ET transplant identifier sourced from the ET contributed rows to the transplantation file.",
        str_endswith="==",
    )

    class Config:
        multiindex_strict = True
        multiindex_coerce = True


class OrganEntnahmeID(SpenderID, TransplantPostOPID):
    class Config:
        multiindex_strict = True
        multiindex_coerce = True


class TransplantationIDReference(EmpfaengerID, OrganEntnahmeID):
    class Config:
        multiindex_strict = True
