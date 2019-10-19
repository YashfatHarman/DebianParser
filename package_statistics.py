import os
import os.path
import re
import time
import operator
import urllib.request
from bs4 import BeautifulSoup
import shutil
import sys

MIRROR = "http://ftp.uk.debian.org/debian/dists/stable/main/"
STATIC_URL = True


def parse_line(line):
    """Checks validity of a line, and if valid then returns the filename and
    associated package names.

    Considering:
        file names can have space,
        and looks like file and folder names can start with special characters
    the only invalid format seems to be a line without any space.

    So, a line without space is invalid.
    A line with one space block has filename and package_list.
    In a line with more than one space block, the last text block is the
    package_list. Everything else will be considered as filename, with spaces.
    """

    # A line may have trailing spaces. Get rid of them.
    line = line.strip()

    # Replace an entire space-block with a single space
    pattern = r"[\s]+"
    p = re.compile(pattern)
    formatted_line, space_count = p.subn(" ", line)

    if space_count == 0:    # invalid format
        return False, None, None

    last_space = formatted_line.rfind(" ")
    packages = formatted_line[last_space+1:]
    file_name = formatted_line[:last_space]
    package_list = packages.split(",")

    return True, file_name, package_list


def parse_file(file_name):
    """The file is downloaded. Parse and get the top-used files.

    Steps:
        1. Read each line. For each line:
            2. Check if it is of proper format
            3. Parse the filename and projectname(s)
            4. Increment the file count of each project using a dict
            5. Sort the dict and return the top ten.
    """

    package_dict = {}

    fp = open(file_name, "r")
    for line in fp:
        validity, file_name, package_list = parse_line(line)

        if validity is True:
            for package in package_list:
                if package not in package_dict:
                    package_dict[package] = 1
                else:
                    package_dict[package] += 1
        else:    # invalid entry
            # print("invalid line:", line)
            pass

    fp.close()

    sorted_packages = sorted(package_dict.items(), key=operator.itemgetter(1),
                             reverse=True)

    results = sorted_packages[:10]
    return results


def extract_url(file_name):
    """Extracts url of the Contents file from the mirror webpage.
    Actually not necessary in our case, as the urls are pretty static.
    """

    try:
        with urllib.request.urlopen(MIRROR) as response:
            soup = BeautifulSoup(response, "lxml")
    except urllib.error.URLError as e:
        print("URLError: {}. Exiting.".format(e.reason))
        sys.exit(-1)

    for aTag in soup.findAll("a"):
        if file_name in aTag.getText():
            url = aTag["href"]
            break

    fullUrl = "{}{}".format(MIRROR, url)
    return fullUrl


def download_file(dest_folder, file_type):
    """Downlods the file in the given destination folder.

    Steps:
        1. Go to the Debian Mirror, download the page
        2. Parse the page to find the exact link to the Contents file
        3. Download the Contents file in proper destination
        4. Extract it.
    """

    file_name = "Contents-{}.gz".format(file_type)

    # Seems like the package destination urls are pretty static,
    # so extracting them from the loading page isn't exactly necessary.
    # Can just generate them directly here.
    # For the time being, keeping both of them.
    # Sample url: http://ftp.uk.debian.org/debian/dists/stable/main/Contents-amd64.gz

    if STATIC_URL is True:
        url = "{}Contents-{}.gz".format(MIRROR, file_type)
    else:
        url = extract_url(file_name)

    os.makedirs(dest_folder, exist_ok=True)
    full_filename = os.path.join(dest_folder, file_name)

    try:
        with urllib.request.urlopen(url) as response, open(full_filename, 'wb') as outfile:
            shutil.copyfileobj(response, outfile)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print("HTTPError: {}. Exiting.".format(e.reason))
        sys.exit(-1)

    # unzip the downloaded file.
    command = "gunzip {}".format(full_filename)
    os.system(command)


if __name__ == "__main__":
    start = time.time()

    # take arguments
    if len(sys.argv) < 2:
        print("Invalid input. Expected: package_statistics.py architecture")
        sys.exit(-1)
    else:
        file_type = sys.argv[1]

    # download files
    dest_folder = "ContentFiles"
    download_file(dest_folder, file_type)

    # collect stat
    file_name = "Contents-{}".format(file_type)
    full_name = os.path.join(dest_folder, file_name)
    results = parse_file(full_name)

    # print results
    for idx, (package, count) in enumerate(results):
        print("{}. {}    {}".format(idx+1, package, count))

    end = time.time()

    print("total time: ", end - start, "secs")
