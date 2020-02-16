import os


def prepare_folder(folder_name):
    """Convenience function to check for existence of data folder
    and construct it if not present.

    Parameters
    ---------
    folder name : str
        Name of folder to check for and create if not present.
    """

    if os.path.isdir(folder_name):
        return
    else:
        os.mkdir(folder_name)
