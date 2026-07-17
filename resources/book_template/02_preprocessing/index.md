# Creation of intermediate datasets

This chapter contains the report for each {term}`intermediate, processed dataset`.
 The following steps are performed if necessary on each file.

(general:ts)=

## Technical Steps

These steps mainly deal with metadata, but no domain knowledge is employed.

(general:ecf)=

### Removal of Non-Informative Columns

Some columns exported in the files by the registry contain no data and some are
complete copies. These are removed in this step. Other columns that we decided
to remove in this step are location identifiers, which are encoded versions of
hosptial adresses for example. Some columns which we found to be not usable
even after preprocessing were also removed at this step.

(general:cr)=

### Renaming of Columns

The column names from the registry are replaced with more human readable
versions.

```{note}
During processing, columns which are supposed to be combined have to end with
either the institution (for example `_et`) or a number (for example `_1`)
```

(general:tpf)=

### Target Population Filtering

The dataset is filtered to match the target population
(see [](../01_targetpop/index.md)). Empty and duplicate columns are removed
again after the filtering step.

(general:ic)=

### Integration of Seperated Institute Data

In some input files, the {term}`institutions` have contributed different columns
and in some also rows describing the same entity.

If a single institute contributed data, the structure looks similar to the
following table.

| Entity ID | Measurement |
|-----------|-------------|
| PatA      | 5           |
| PatB      | 3           |

For two institutes two cases can occur. For some files, the registry
already connected the entites. An examples follows.

| Entity ID from Institute X | Entity ID from Institute Y | Measurement from Institute X | Measurement from Institute Y |
|----------------------------|----------------------------|------------------------------|------------------------------|
| PatA                       | PatA                       | 5                            | 4.9                          |
| PatB                       |                            | 3                            |                              |
|                            | PatC                       |                              | 7                            |

If the registry has not connected the entities, the same data will look like this.

| Entity ID from Institute X | Entity ID from Institute Y | Measurement from Institute X | Measurement from Institute Y |
|----------------------------|----------------------------|------------------------------|------------------------------|
| PatA                       |                            | 5                            |                              |
|                            | PatA                       |                              | 4.9                          |
| PatB                       |                            | 3                            |                              |
|                            | PatC                       |                              | 7                            |
|                            | PatA                       |                              | 4.8                          |

Problems like the last row, where there are multiple rows for a single entity
contributed by an institute, lead to the registry not connected the data. This
is caused by longitudinal data being present, which was contributed by either
one or more institutes.

(general:ds)=

## Domain Steps

Here, data is actually modified either based on domain knowledge or knowledge
derived from the data.

(general:rf)=

### Row Filtering

Some files contain rows which are not relevant for our processing, they are
either removed or collapsed in this step.

(general:uc)=

### Unit Conversions

Some measurements are reported in different units
(for example `g/l` or `mol/l`). To make them more easily available, they are
converted to a single shared unit if possible. A similar approach is applied
to categorical columns, where different representations are used accross
different columns for the same measurements (for example `m` or `männlich`)

(general:crc)=

### Consolidating Columns

Some measurements are reported in multiple columns, but sometimes contain a
few inconsistencies. By consolidating those columns into a single column, the
measurement becomes usable as a feature. Depending on the type of
columns, different strategies are selected.

If only one or no column has a measurement for every row, this single
measurement is used for a new column. For measurements with non numerical
data, disagreements between columns are treated as missing values for the
new consolidated column. If the redundant columns are numeric, the mean is
taken. However, if the standard deviation among the redundant values for a
row exceeds the standard deviation of the column with the highest standard
deviation it is regarded as missing.
