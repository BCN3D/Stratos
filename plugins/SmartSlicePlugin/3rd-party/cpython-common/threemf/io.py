import zipfile
import typing
import xml.etree.cElementTree as xml

from . import ThreeMF, ThreeMFException

class Writer:
    def write(self, tmf : ThreeMF, tmffile : typing.io.BinaryIO):
        """
            tmf: ThreeMF object
            tmffile: file like object
        """

        z = zipfile.ZipFile(tmffile, mode='w', compression=zipfile.ZIP_DEFLATED)

        z.writestr(tmf._CONTENT_TYPES_PATH, xml.tostring(tmf._content_types_xml, encoding='utf8'))
        z.writestr(tmf._RELS_PATH, xml.tostring(tmf._relationships_xml, encoding='utf8'))

        for m in tmf.models:
            z.writestr(m.path, xml.tostring(m.serialize(), encoding='utf8'))

        for ext in tmf.extensions:
            ext.write(z)

        z.close()

class Reader:
    def __init__(self):
        self._extensions = []

    def register_extension(self, cls):
        ext = cls()
        self._extensions.append(ext)
        return ext

    def read(self, tmf : ThreeMF, tmffile : typing.io.BinaryIO):
        z = zipfile.ZipFile(tmffile)

        content_types_xml = z.read(tmf._CONTENT_TYPES_PATH).decode('utf-8')
        relationships_xml = z.read(tmf._RELS_PATH).decode('utf-8')

        tmf._load(
            z,
            content_types_xml,
            relationships_xml
        )

        for ext in self._extensions:
            ext.read(z)
            tmf.extensions.append(ext)

        for ext in self._extensions:
            ext.process_threemf(tmf)

    def verify(self, tmffile: typing.io.BinaryIO, max_file_size_mb: int = 100):
        z = zipfile.ZipFile(tmffile)

        max_bytes = max_file_size_mb * 1024 * 1024

        for f in z.filelist:
            if f.file_size > max_bytes:
                raise ThreeMFException('File %s in 3MF exceeds max file size of %i MB' % (f.filename, max_file_size_mb))
