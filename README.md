# fl-utils
Tools for accessing and working with data from the Fallen London database.

```melt.py``` contains utilities for retrieving and decrypting data.

```fl.py``` contains methods to format the data.

## How to use
```python -i melt.py``` will initialize the scraper and check for / retrieve any database updates.

(This will take a while during the first run)

If there was already data in ```./text/fl.dat```, the old versions will be stored in the dict ```old```.

```print_diff()``` can then be called using the key (e.g. ```print_diff('events:284781')```) to print a diff of the old and new keys.

To format Storylets, Qualities, etc., ```print(fl.Storylet.get(284781))``` or ```print(fl.Quality.get(804))```, for example.
