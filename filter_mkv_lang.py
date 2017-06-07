import getopt
import json
import os
import re
import sys
import StringIO
import subprocess

# set up default values
LANG = "eng"
MKVMERGE = "/usr/bin/mkvmerge"
DIR = "."

# grab the options passed in
try:
    opts, args = getopt.getopt(sys.argv[1:],"d:l:m:",["dir=","lang=","mkvmerge="])
except getopt.GetoptError:
    print "filter_mkv_lang.py -d <target dir> -l <3-letter lang> -m <path to mkvmerge>"
    sys.exit(2)

# parse them & overwrride defaults
for opt, arg in opts:
    if opt in ("-d", "--dir"):
        DIR = arg
    elif opt in ("-l", "--lang"):
        LANG = arg
    elif opt in ("-m", "--mkvmerge"):
        MKVMERGE = arg

# sanity checks 
# dir should actually be a dir
if not os.path.isdir(DIR):
    print "invalid target directory"
    sys.exit(2)

# language must be 3 characters
if len(LANG) != 3:
    print "language should be the 3 character code"
    sys.exit(2)

# mkvmerge should be executable
if not os.path.isfile(MKVMERGE) or os.path.isfile(MKVMERGE) and not os.access(MKVMERGE, os.X_OK):
    print "invalid mkvmerge location"
    sys.exit(2)

# walk through the dir specified
for root, dirs, files in os.walk(DIR):
    # go through the files found
    for f in files:
        # only work with .mkv files
        if not f.endswith(".mkv"):
            continue

        # grab the full path to the current .mkv file
        path = os.path.join(root, f)

        # start output for this file
        print "# " + path

        # ask mkvmerge for the json info
        cmd = [MKVMERGE, "-i", "-F", "json", path]
        mkvmerge = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = mkvmerge.communicate()
        if mkvmerge.returncode != 0:
            print >> sys.stderr, " - mkvmerge failed to identify\n"
            continue

        # load the response & grab the track info
        info = json.load(StringIO.StringIO(stdout))
        tracks = {"audio": {LANG: 0, "non": 0}, "subtitles": {LANG: 0, "non": 0}}
        # check out each track
        for track in info["tracks"]:
            # if we care about it (ignore video, etc.), bump the count of the lang
            # if it's not the lang we're filtering to, bucket it into "non"
            if track["type"] in ("audio", "subtitles"):
                key = LANG if track["properties"]["language"] == LANG else "non"
                tracks[track["type"]][key] += 1

        # yes, these could all be a single block, but I wanted distinct messaging
        # we can't filter to the specified language since there are no tracks for it
        if tracks["audio"][LANG] == 0 and tracks["subtitles"][LANG] == 0:
            print >> sys.stderr, " - nothing to do (no tracks found for " + LANG + ")\n"
            continue

        # we don't need to process this as it's already just the language we want
        if tracks["audio"]["non"] == 0 and tracks["subtitles"]["non"] == 0:
            print >> sys.stderr, " - nothing to do (no non-" + LANG + " tracks found)\n"
            continue

        # we don't need to process this since there's only a single track of each
        # and we don't want to be left without audio/subtitles
        if sum(tracks["audio"].values()) == 1 and sum(tracks["subtitles"].values()) == 1:
            print >> sys.stderr, " - nothing to do (only 1 audio & subtitle track)\n"
            continue

        # build command line to process the file
        cmd = [MKVMERGE, "-a", LANG, "-s", LANG, "-o", path + ".temp", path]

        # process file
        print >> sys.stderr, " - Processing", path, "...\n",
        mkvmerge = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = mkvmerge.communicate()
        if mkvmerge.returncode != 0:
            print >> sys.stderr, "  -- Failed\n"
            continue

        print >> sys.stderr, "  -- Succeeded\n"

        # remove file with extra tracks, move new file into it's place
        os.remove(path)
        os.rename(path + ".temp", path)
