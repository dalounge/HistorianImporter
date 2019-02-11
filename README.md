# HistorianImporter
Created for Flint.

RDS applications needed to be merged into a single Historian file and parsed based on logged history checkbox.

Took each of the DB Dump and parsed out originally just the analog tags.  Added in also the discrete.
Looks for the access names and creates them.

Parses each one out with the logged data and reconstructs them into Historian Load format.

Website was created to upload the .zip file of all the DB.  File names with the prefix separated by an _ will have a prefix tied to the
tag and the Access Names to differentiate the instances for each OI Server.

- Modifications need to be that the Access Names are redundant.  Probably just need to set the list before appending.
- For the analog tags, it was not taken into consideration for if they reach out further than just a signed integer.  -32 to + 32.
  - Add this in if dealing with outside this scope.

