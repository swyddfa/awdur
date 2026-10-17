60F
Bf@0,9:itertoolsl@BY,2:re23W@CA,1:r95@2Fh,r@38G,V@2Pe,6:rid={rsu@2QG,L: and (value := row[0]b@2~G,5:value12f@3Id,G:tuple[str, str]]1E@4fA,7_@4M_,4:idx,3E@4U7,G:(idx, blob.text)b5@4XU,O@58D,B:(idx, uuid)BR@58e,I:tuple[str, str]],
8@33l,W@5KA,9@3Fj,L@5Kg,1:,1J@5L0,p:(l for _, l in sorted(lines, key=folgzettel_sort)))
9@~~,RC@5MZ,3E:folgzettel_sort(item: str | tuple[str, ...]) -> tuple[int | str, ...]:
    """A key function for use with Python's sorted() function to return a series of
    'folgzettel' numbers in the correct order."""

J@5Py,5F:tem, tuple):
        value = item[0]
    else:
        value = item

    prefix, *rest = re.split(r"(\d+)", value)
    if prefix != "":
        raise ValueError("Folgzettel numbers must start with a digit")

    converters = itertools.cycle([int, str])
    return tuple(convert(value) for convert, value in zip(converters, rest))


defJ@5pk,3c@5n1,2AqWjA;