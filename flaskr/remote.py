import dropbox

class DropboxRemote:
    def __init__(self, accessToken, localPath, remotePath):
        self.handle = dropbox.Dropbox(accessToken)
        self.localPath = localPath
        self.remotePath = remotePath

    def load(self):
        print("Loading db from: ", self.remotePath)
        self.handle.files_download_to_file(
                self.localPath,
                self.remotePath)
        # (metadata, response) = self.handle.files_download(self.remotePath)
        # with open(self.localPath, 'wb') as f:
        #     for chunk in r.iter_content(chunk_size=256):
        #         f.write(chunk)
    
    def save(self):
        print("Saving db to: ", self.remotePath)
        with open(self.localPath, 'rb') as f:
            data = f.read()
        self.handle.files_upload(data, self.remotePath, dropbox.files.WriteMode.overwrite)
