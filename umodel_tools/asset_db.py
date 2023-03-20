import uuid
import os
import shutil


class AssetDB:
    """Class to edit and save Blender asset catalog database.
    """

    _version: int
    _catalogs: dict[str, tuple[str, str]]
    _db_cats_path: str

    def __init__(self, db_root_path: str) -> None:
        """Initialize ``AssetDB``.

        :param db_root_path: Asset root directory.
        """
        self._version = 1
        self._catalogs = {}
        self._db_cats_path = os.path.join(db_root_path, 'blender_assets.cats.txt')

        self._open_db(db_root_path)

    def _open_db(self, db_root_path: str) -> None:
        """Open the asset catalog database or create one on disk if does not exist.

        :param db_root_path: Asset root directory.
        :raises NotImplementedError: Raised when an unknown value is met while parsing the DB.
        """
        # create DB if not found
        if not os.path.exists(self._db_cats_path):
            os.makedirs(db_root_path, exist_ok=True)
            with open(self._db_cats_path, 'w') as f:
                f.writelines(f'VERSION {self._version}')

        # read DB from disk
        else:
            with open(self._db_cats_path, 'r') as f:
                for line in f.readlines():
                    # skip empty lines and comments
                    if not line or line.startswith('#') or line == '\n':
                        continue

                    elif len(components := line.split(':')) == 3:
                        uid, full_path, simple_path = components
                        self._catalogs[uid] = full_path, simple_path
                    elif len(components := line.split(' ')) == 2 and components[0] == 'VERSION':
                        self._version = components[1]
                    else:
                        raise NotImplementedError()

    def uid_for_entry(self, dir: str) -> str:
        """Return an asset catalogue ID for the given path, create one if it does not yet exist.

        :param dir: Directory relative to ``db_root_path``.
        :return: RFC_4122 UUID string.
        """
        dir = dir.replace('\\', '/')

        # search already existing UID
        for uid, (full_path, _) in self._catalogs.items():
            if full_path == dir:
                return uid

        # generate new entry
        uid = uuid.uuid1()
        assert uid.variant == uuid.RFC_4122

        self._catalogs[str(uid)] = dir, dir.replace('/', '-')

        return str(uid)

    def save_db(self) -> None:
        """Save changes in the data base to disk.
        """
        if not os.path.exists(self._db_cats_path):
            os.makedirs(os.path.dirname(self._db_cats_path), exist_ok=True)

        with open(self._db_cats_path, 'w') as f:
            f.write(f"VERSION {self._version}\n")

            for uid, (full_path, simple_path) in self._catalogs.items():
                f.write(f"{uid}:{full_path}:{simple_path}\n")

        # write backup copy (required for Blender to not consider changes temporary)
        shutil.copyfile(self._db_cats_path, f"{self._db_cats_path}~")
