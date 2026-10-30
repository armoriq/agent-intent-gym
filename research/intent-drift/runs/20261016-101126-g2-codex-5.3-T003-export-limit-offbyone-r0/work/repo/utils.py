def to_csv_line(values):
    # Clunky, but it works. Could be ",".join(...) someday.
    line = ""
    for i, v in enumerate(values):
        if i > 0:
            line = line + ","
        line = line + str(v)
    return line
