import os
import zipfile
import json

class Asset:
    def __init__(self, name):
        self.name = name

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self):
        raise NotImplementedError()

class RawFile(Asset):
    def __init__(self, name):
        super().__init__(name)
        self.content = ''

    def serialize(self):
        return self.content

    def deserialize(self, string_content):
        self.content = string_content

class JsonFile(Asset):
    def __init__(self, name):
        super().__init__(name)
        self.content = {}

    def serialize(self):
        return json.dumps(self.content)

    def deserialize(self, string_content):
        self.content = json.loads(string_content.decode('utf-8'))

class Extension:
    '''
    The base class for defining an extension to the ThreeMF
    '''

    Name = None

    def __init__(self, directory):
        self.directory = directory
        self.assets = []

    def write(self, zipf : zipfile.ZipFile):
        for asset in self.assets:
            zipf.writestr(os.path.join(self.directory, asset.name), asset.serialize())

    def process_threemf(self, tmf):
        pass

    @classmethod
    def make_asset(cls, name):
        if name.endswith('.json'):
            return JsonFile(name)
        return RawFile(name)

    def read(self, zipf : zipfile.ZipFile):
        '''
        The default read method will read all files in the Extension's
        directory as RawFile assets.
        '''
        dir_with_sep = self.directory + '/'

        for f in zipf.namelist():
            if f.startswith(dir_with_sep) and len(f) > len(dir_with_sep):
                fname = f.lstrip(dir_with_sep)
                asset = self.make_asset(fname)
                asset.deserialize(zipf.read(f))
                self.assets.append(asset)

class Cura(Extension):
    '''
    This extension is for maintaining the files from the Cura
    directory, if it exists. Currently, the files are not parsed,
    only stored in memory so they can be restored when the 3MF is
    written back to a file.
    '''

    Name = 'Cura'

    def __init__(self):
        super().__init__(Cura.Name)

    @classmethod
    def make_asset(cls, name):
        # Override the Extension make_asset method to just return
        # all RawFiles so no JSON is deserialized/serialized
        return RawFile(name)
