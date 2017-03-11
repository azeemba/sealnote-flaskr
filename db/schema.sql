PRAGMA KEY = "password";
DROP TABLE IF EXISTS notes;
CREATE TABLE notes (
                _id  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                position INTEGER,
                title  TEXT,
                content   TEXT,  
                content_extra   TEXT,  
                color   INTEGER,  
                created   TEXT,  
                edited   TEXT,  
                archived   INTEGER NOT NULL DEFAULT '0', 
                deleted   INTEGER NOT NULL DEFAULT '0', 
                type   TEXT NOT NULL DEFAULT 'Note.Type.TYPE_GENERIC.name()' 
                ); 
