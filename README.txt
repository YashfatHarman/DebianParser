Small Python script to download Debian contents file from the repo,
and to parse the file and gather some basic statistics.

1. Takes file type argument from the user.
2. Downloads the apporipriate Contents file.
3. Parses the file. For each valid line, identifies the file name and package names,
updates statistics.
4. Prints the top 10 packages with most number of files associated with them.

Did as part of a larger objective. 
