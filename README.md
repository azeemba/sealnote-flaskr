sealnote-flaskr
==============

## Overview:

vishesh/sealnote is an android application that provides encrypted journal functionality. It does so by using a sqlcipher db which can be exported/imported.

This application assumes that such a db has been exported and creates a web interface around the db.

The webserver code is mostly the example code in https://github.com/pallets/flask/blob/master/examples/flaskr/flaskr/flaskr.py
Minimal changes were made to fit the new use case


## How to Use:

- Requires libsqlcipher-dev to be already installed so the pysqlcipher3 package will work on your machine

```
pip install -r requirements.txt
```

- Edit flaskr/flaskr.py to point to the location of the DB

```
python3 flaskr/flaskr.py
```

Now you should be able to run http://127.0.0.1:5000 and then type in your password and read or add notes. Once done, the db ideally should be able to be imported back into sealnote.


## Work left to do:

- Testing. I haven't verified the import into seal note
- Styling improvements on the website
- Commandline argument for the location of the database file
- Automatically generate a good "private secret key"
- Consider sending PR to sealnote to auto-export/import on close/open of the application to work better with this application
