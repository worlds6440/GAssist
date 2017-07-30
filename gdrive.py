from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.http import MediaFileUpload

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GDrive():

    def __init__(self):
        """ Class constructor """
        # Initialise Google Drive Connection
        # If modifying these scopes, delete your previously saved credentials
        # at ~/.credentials/drive-python-quickstart.json
        # self.SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
        self.SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive.file'
        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.APPLICATION_NAME = 'Drive API Python Quickstart'

        self.credentials = self.get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=self.http)

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'drive-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(
                self.CLIENT_SECRET_FILE,
                self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def find_file(self, file_name, parent='root', is_folder=False):
        """ Find a file/folder with parent """
        if file_name == "":
            return []

        mimeType = "mimeType != 'application/vnd.google-apps.folder'"
        if is_folder:
            mimeType = "mimeType = 'application/vnd.google-apps.folder'"
        q = ("modifiedTime > '2012-01-01T12:00:00'"
             " and {}"
             " and '{}' in parents"
             " and name contains '{}'"
             " and trashed = false"
             ).format(mimeType, parent, file_name)
        #print("q=" + q)

        results = self.service.files().list(
            q=q,
            pageSize=100,
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items

    def upload(self, local_filepath, remote_path, mimeType='image/jpeg'):
        """ Upload a file """
        new_file_id = ""

        # Split local filename into path and filename
        local_split = local_filepath.split('/')
        # retrieve the filename from the local path/filename
        file_name = local_split[-1]

        # Attempt to find each sequential folder on remote server.
        full_path_exists = True
        parent = 'root'

        # Split folder path into path segments,
        remote_path_split = remote_path.split('/')
        for x in remote_path_split:
            if x != "" and x != "root":
                # Find folder.
                # print("Finding " + parent + "/" + x)
                items = self.find_file(x, parent=parent, is_folder=True)
                if len(items):
                    # Folder exists, update parent to this folder.
                    parent = items[0]['id']
                    # print ("Found")
                else:
                    full_path_exists = False
                    # print ("Failed")
                    break  # Folder doesn't exist

        if full_path_exists:
            items = self.find_file(file_name, parent=parent, is_folder=False)
            if len(items) == 0:
                # File doesn't exist
                file_metadata = {
                    'name': file_name,
                    'parents': ['{}'.format(parent)]
                }
                media = MediaFileUpload(
                    local_filepath,
                    mimetype=mimeType)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id').execute()
                new_file_id = file.get('id')
                # print('File ID: {}'.format(new_file_id))
            else:
                print("File already exists on remote")
        else:
            print("Remote folder path doesn't exist")
        # Return the uploaded files ID
        return new_file_id

    def create_folder(self, folder_name):
        """ Create a new folder """
        new_folder_id = ""
        parent = 'root'

        # Split folder path into path segments
        remote_path_split = folder_name.split('/')
        for x in remote_path_split:
            if x != "" and x != "root":
                # Find folder.
                # print("Finding " + parent + "/" + x)
                items = self.find_file(x, parent=parent, is_folder=True)
                if len(items):
                    #print("Folder Exists")
                    # Folder exists, update parent to this folder.
                    parent = items[0]['id']
                else:
                    # Folder doesn't exists. Create it now.
                    parent = self.create_single_folder(x, parent)
                    new_folder_id = parent
        return new_folder_id

    def create_single_folder(self, folder_name, parent='root'):
        """ Simple method to get Google to
            create a folder with a given parent. """

        # DEBUG
        #print("Creating " + folder_name + ": parent = " + parent)

        new_folder_id = ""
        q = ("modifiedTime > '2012-01-01T12:00:00'"
             " and mimeType = 'application/vnd.google-apps.folder'"
             " and '{}' in parents"
             " and name = '{}'"
             " and trashed = false"
             ).format(parent, folder_name)
        # print("q=" + q)

        results = self.service.files().list(
            q=q,
            pageSize=100,
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            # print('Folder not found')
            file_metadata = {
                'name': [folder_name],
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': ['{}'.format(parent)]
            }
            #print(file_metadata)
            file = self.service.files().create(
                body=file_metadata,
                fields='id').execute()
            new_folder_id = file.get('id')
            # print('New folder ID: {}'.format(new_folder_id))
        else:
            new_folder_id = items[0]['id']
            # print('Existing folder ID: {}'.format(new_folder_id))
        return new_folder_id

    def list_all_files(self):
        """ Simple method to list all files and folders in specific folder """
        results = self.service.files().list(
            q=("modifiedTime > '2012-06-04T12:00:00' and "
               "name = 'Wills' and "
               "'root' in parents and "
               "trashed = false"
               ),
               #"(mimeType contains 'image/' or mimeType contains 'video/')"),
            pageSize=10,
            fields="nextPageToken, files(id, name, trashed)").execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print('{0} ({1}) trashed={2}'.format(item['name'], item['id'], item['trashed']))

    def example(self):
        """ Shows basic usage of the Google Drive API. """
        # Prep remote folder and file
        remote_folder = 'Wills/Hal9000/'
        local_filepath = "hypnotic_med1.jpg"
        # Create folders and upload a file to the drive
        folder_id = self.create_folder(remote_folder)
        self.upload(local_filepath, remote_folder)

        #parent = 'root'
        #remote_path_split = remote_folder.split('/')
        #for x in remote_path_split:
        #    if x and x != "":
        #        files = self.find_file(x, parent=parent, is_folder=True)
        #        print(files)

        # self.list_all_files()

        # https://developers.google.com/drive/v3/web/search-parameters


if __name__ == '__main__':
    gd = GDrive()
    gd.example()
