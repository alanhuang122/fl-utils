# fl-utils
Tools for accessing and working with data from the Fallen London database.

```melt.py``` contained utilities for retrieving and decrypting data.

Now that the mobile app has been retired, this file is defunct.

```fl.py``` contains methods to format the data.

## How to use
~~```python -i melt.py``` will initialize the scraper and check for / retrieve any database updates.~~

~~(This will take a while during the first run)~~

~~If there was already data in ```./text/fl.dat```, the old versions will be stored in the dict ```old```.~~

~~```print_diff()``` can then be called using the key (e.g. ```print_diff('events:284781')```) to print a diff of the old and new keys.~~

Using this tool now requires a pre-existing copy of the data from the Fallen London database.

To format Storylets, Qualities, etc., ```print(fl.Storylet.get(284781))``` or ```print(fl.Quality.get(804))```, for example.
