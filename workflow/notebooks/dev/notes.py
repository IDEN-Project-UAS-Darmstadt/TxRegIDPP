col = ""
col = data.columns[col]
print(data[col].isna().any())
display(data[col].describe())
print(repr(data[col].drop_duplicates().dropna().to_list()))
