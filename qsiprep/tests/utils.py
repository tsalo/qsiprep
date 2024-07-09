"""Utility functions for tests."""

import lzma
import os
import tarfile
from glob import glob
from gzip import GzipFile
from io import BytesIO

import requests
from nipype import logging

from qsiprep import config

LOGGER = logging.getLogger("nipype.utils")


def download_test_data(dset, data_dir=None):
    """Download test data."""
    URLS = {
        "HBCD": "https://upenn.box.com/shared/static/gn1ec8x7mtk1f07l97d0th9idn4qv3yx.xz",
        "DSCSDSI": "https://upenn.box.com/shared/static/eq6nvnyazi2zlt63uowqd0zhnlh6z4yv.xz",
        "DSCSDSI_BUDS": "https://upenn.box.com/shared/static/bvhs3sw2swdkdyekpjhnrhvz89x3k87t.xz",
        "DSDTI": "https://upenn.box.com/shared/static/iefjtvfez0c2oug0g1a9ulozqe5il5xy.xz",
        "twoses": "https://upenn.box.com/shared/static/c949fjjhhen3ihgnzhkdw5jympm327pp.xz",
        "multishell_output": (
            "https://upenn.box.com/shared/static/hr7xnxicbx9iqndv1yl35bhtd61fpalp.xz"
        ),
        "singleshell_output": (
            "https://upenn.box.com/shared/static/9jhf0eo3ml6ojrlxlz6lej09ny12efgg.gz"
        ),
        "drbuddi_rpe_series": (
            "https://upenn.box.com/shared/static/j5mxts5wu0em1toafmrlzdndves1jnfv.xz"
        ),
        "drbuddi_epi": "https://upenn.box.com/shared/static/plyuee1nbj9v8eck03s38ojji8tkspwr.xz",
        "DSDTI_fmap": "https://upenn.box.com/shared/static/rxr6qbi6ezku9gw3esfpnvqlcxaw7n5n.gz",
        "DSCSDSI_fmap": "https://upenn.box.com/shared/static/l561psez1ojzi4p3a12eidaw9vbizwdc.gz",
    }
    if dset == "*":
        for k in URLS:
            download_test_data(k, data_dir=data_dir)

        return

    if dset not in URLS:
        raise ValueError(f"dset ({dset}) must be one of: {', '.join(URLS.keys())}")

    if not data_dir:
        data_dir = os.path.join(os.path.dirname(get_test_data_path()), "test_data")

    out_dir = os.path.join(data_dir, dset)

    if os.path.isdir(out_dir):
        config.loggers.utils.info(
            f"Dataset {dset} already exists. "
            "If you need to re-download the data, please delete the folder."
        )
        return out_dir
    else:
        config.loggers.utils.info(f"Downloading {dset} to {out_dir}")

    os.makedirs(out_dir, exist_ok=True)
    url = URLS[dset]
    with requests.get(url, stream=True) as req:
        if url.endswith(".xz"):
            with lzma.open(BytesIO(req.content)) as f:
                with tarfile.open(fileobj=f) as t:
                    t.extractall(out_dir)
        elif url.endswith(".gz"):
            with tarfile.open(fileobj=GzipFile(fileobj=BytesIO(req.content))) as t:
                t.extractall(out_dir)
        else:
            raise ValueError(f"Unknown file type for {dset} ({url})")

    return out_dir


def get_test_data_path():
    """Return the path to test datasets, terminated with separator.

    Test-related data are kept in tests folder in "data".
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "data") + os.path.sep)


def check_generated_files(qsiprep_dir, output_list_file, optional_output_list_file):
    """Compare files generated by qsiprep with a list of expected files."""
    found_files = sorted(glob(os.path.join(qsiprep_dir, "**/*"), recursive=True))
    found_files = [os.path.relpath(f, qsiprep_dir) for f in found_files]

    # Ignore figures
    found_files = sorted(list(set([f for f in found_files if "figures" not in f])))

    # Ignore logs
    found_files = sorted(list(set([f for f in found_files if "log" not in f.split(os.path.sep)])))

    with open(output_list_file, "r") as fo:
        expected_files = fo.readlines()
        expected_files = [f.rstrip() for f in expected_files]

    optional_files = []
    if optional_output_list_file:
        with open(optional_output_list_file, "r") as fo:
            optional_files = fo.readlines()
            optional_files = [f.rstrip() for f in optional_files]

    if sorted(found_files) != sorted(expected_files):
        expected_not_found = sorted(list(set(expected_files) - set(found_files)))
        found_not_expected = sorted(list(set(found_files) - set(expected_files)))

        msg = ""
        if expected_not_found:
            msg += "\nExpected but not found:\n\t"
            msg += "\n\t".join(expected_not_found)

        if found_not_expected:
            # Check that the found files are in the optional file list
            found_not_expected = [f for f in found_not_expected if f not in optional_files]

        if found_not_expected:
            msg += "\nFound but not expected:\n\t"
            msg += "\n\t".join(found_not_expected)

        if msg:
            raise ValueError(msg)


def reorder_expected_outputs():
    """Load each of the expected output files and sort the lines alphabetically.

    This function is called manually by devs when they modify the test outputs.
    """
    test_data_path = get_test_data_path()
    expected_output_files = sorted(glob(os.path.join(test_data_path, "*_outputs.txt")))
    for expected_output_file in expected_output_files:
        LOGGER.info(f"Sorting {expected_output_file}")

        with open(expected_output_file, "r") as fo:
            file_contents = fo.readlines()

        file_contents = sorted(list(set(file_contents)))

        with open(expected_output_file, "w") as fo:
            fo.writelines(file_contents)
