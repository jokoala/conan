import os
import tarfile
import zipfile

from unittest import TestCase

from conans.test.utils.test_files import temp_folder
from conans.tools import unzip
from conans.util.files import save_files


def create_archive(archive, root, relative_file_paths):
    """ Create an archive with given file paths relative to given root."""
    extension = os.path.basename(archive).split(os.extsep, 1)[1]
    if extension == "zip":
        with zipfile.ZipFile(archive, mode="w") as z:
            for file_ in relative_file_paths:
                z.write(os.path.join(root, file_), arcname=file_)
    else:
        # Treat any other extension except "tar.gz" as a normal "tar"
        mode = "gz" if extension == "tar.gz" else ""
        with tarfile.open(archive, mode="w:%s" % mode) as t:
            for file_ in relative_file_paths:
                t.add(os.path.join(root, file_), arcname=file_)
    return archive


class FilesExtractPatternTest(TestCase):

    def test_patterns(self):
        def cross_platform_path(relative_path_with_slashes):
            """ Convert string with slashes to platform-specific path. Windows
            will not interpret correctly the slash. """
            return os.path.join(*relative_path_with_slashes.split("/"))

        # Test setup
        src_dir = temp_folder()
        files = {cross_platform_path(k): v for (k, v) in {
            "foo/file.cpp": "code",
            "foo/bar/file.txt": "text",
            "foo/bar/file.cpp": "more code",
            "foo/bar/baz/file.txt": "more text"
        }.items()}
        matches = {k: list(map(cross_platform_path, v)) for (k, v) in {
            "*.cpp": ["foo/file.cpp",
                      "foo/bar/file.cpp"],
            "*.txt": ["foo/bar/file.txt",
                      "foo/bar/baz/file.txt"],
            "foo/bar/*": ["foo/bar/file.txt",
                          "foo/bar/file.cpp",
                          "foo/bar/baz/file.txt"],
            "foo/bar/baz/*": ["foo/bar/baz/file.txt"],
            "*": ["foo/file.cpp",
                  "foo/bar/file.txt",
                  "foo/bar/file.cpp",
                  "foo/bar/baz/file.txt"],
            "nothing": []
        }.items()}
        save_files(src_dir, files)

        for extension in ["zip", "tar", "tar.gz"]:
            # GIVEN an archive with files inside
            archive_dir = temp_folder()
            archive = os.path.join(archive_dir, "archive.%s" % extension)
            create_archive(archive, src_dir, files)

            for (pattern, paths) in matches.items():
                # WHEN a pattern is used for file extraction
                dst_dir = temp_folder()
                unzip(archive, dst_dir, pattern=pattern)

                # THEN only and all files matching the pattern are extracted
                expected = set(map(lambda x: os.path.join(dst_dir, x), paths))
                actual = set()
                for extracted_dir, _, extracted_files in os.walk(dst_dir):
                    actual.update(map(lambda x: os.path.join(extracted_dir, x),
                                      extracted_files))

                self.assertSetEqual(expected, actual)