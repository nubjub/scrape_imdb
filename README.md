search_to_csv.py takes an imdb search url (in compact mode) and produces a csv from it.

What's wrong with it:
The url requests can throw errors that need to be caught.
The csv is not in a ridgid order
The unicode doesn't work quite right.
This scraper doesn't currently get: rating, description.
...Plenty more I'm sure.