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


Flask site to draw in a zip file, route the extracted files and process.  Spits back out a zip files with finished data.  Clears folders except for final copy.
```
@app.route('/historianimporter', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        import zipfile
        z = zipfile.ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        z.extractall(os.path.join(app.root_path, 'historianImport/dbfiles'))
        himport = historian.HistorianImport(
        os.path.join(app.root_path, 'historianImport/complete'),
        os.path.join(app.root_path, 'historianImport/dbfiles'),
        os.path.join(app.root_path, 'historianImport/temp'))
        himport.init()
        import shutil
        shutil.make_archive(
            os.path.join(app.root_path, 'historianImport/zipfile/historianfiles'),
            'zip',
            os.path.join(app.root_path, 'historianImport/complete'))

        for folders, subfolders, filenames in os.walk(os.path.join(app.root_path, 'historianImport/complete')):
            for filename in filenames:
                os.remove(os.path.join(app.root_path, 'historianImport/complete', filename))

        for folders, subfolders, filenames in os.walk(os.path.join(app.root_path, 'historianImport/dbfiles')):
            for filename in filenames:
                os.remove(os.path.join(app.root_path, 'historianImport/dbfiles', filename))

        for folders, subfolders, filenames in os.walk(os.path.join(app.root_path, 'historianImport/temp')):
            for filename in filenames:
                os.remove(os.path.join(app.root_path, 'historianImport/temp', filename))

    return send_file(os.path.join(app.root_path, 'historianImport/zipfile/historianfiles.zip'))
```

To call the function without the website.  Load up the class.
Create these folders which is set in the initializing of the class
- historianpath  - Finished directory
- dbfiles - Store the DB Files to get processed
- tempfiles - Staging area where everything gets parsed and processed

run init() to start the process.
```
class HistorianImport():
    '''
    Initialize import by calling init() function
    '''
    def __init__(self, historianpath, dbfiles, tempfiles):
        # Path of complete files
        self.historian_path = historianpath
        # Path of DB files to parse
        self.db_files = dbfiles
        # Temp space
        self.temp_files = tempfiles
```
