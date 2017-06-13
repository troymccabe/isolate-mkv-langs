import getopt
import json
import os
import sys
import StringIO
import subprocess

# set up default values
DIR = "."
KEEP = False
LANGS = "eng"
MKVMERGE = "/usr/bin/mkvmerge"

# grab the options passed in
try:
    opts, args = getopt.getopt(sys.argv[1:],"d:hkl:m:",["dir=","help","keep","langs=","mkvmerge="])
except getopt.GetoptError:
    print "isolate_mkv_langs.py -d <target dir> -l <3-char_lang_code> -m <path to mkvmerge>"
    sys.exit(2)

# parse them & overwrride defaults
for opt, arg in opts:
    if opt in ("-d", "--dir"):
        DIR = arg
    elif opt in ("-h", "--help"):
        print """isolate_mkv_langs.py -d </path/to/mkvs> -l <3-char_lang_code> -m </path/to/mkvmerge>
                  
 Options:
  -d, --dir <folder>            The directory where your MKVs are stored
  -h, --help                    Display help text
  -k, --keep        	        Keep original file
  -l, --langs <languages>       3-character language code (e.g. eng). To retain multiple, separate languages with a comma (e.g. eng,spa)
  -m, --mkvmerge <executable>   The path to the MKVMerge executable"""
        sys.exit()
    elif opt in ("-k", "--keep"):
        KEEP = True
    elif opt in ("-l", "--lang"):
        # make sure there are no spaces in the string
        LANGS = arg.replace(" ", "")
    elif opt in ("-m", "--mkvmerge"):
        MKVMERGE = arg

# sanity checks 
# dir should actually be a dir
if not os.path.isdir(DIR):
    print "invalid target directory"
    sys.exit(2)

# language must be at least 3 characters
# no validation on langs--if you're using this, you should know what lang to use
if len(LANGS) < 3:
    print "language should be the 3 character code (or several comma separated 3 character codes)"
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
        tracks = {"audio": {LANGS: 0, "non": 0}, "subtitles": {LANGS: 0, "non": 0}}
        # check out each track
        for track in info["tracks"]:
            # if we care about it (ignore video, etc.), bump the count of the lang
            # if it's not the lang we're filtering to, bucket it into "non"
            if track["type"] in ("audio", "subtitles"):
                key = LANGS if track["properties"]["language"] in LANGS else "non"
                tracks[track["type"]][key] += 1

        # yes, these could all be a single block, but I wanted distinct messaging
        # we can't filter to the specified language since there are no tracks for it
        if tracks["audio"][LANGS] == 0 and tracks["subtitles"][LANGS] == 0:
            print >> sys.stderr, " - nothing to do (no tracks found for " + LANGS + ")\n"
            continue

        # we don't need to process this as it's already just the language we want
        if tracks["audio"]["non"] == 0 and tracks["subtitles"]["non"] == 0:
            print >> sys.stderr, " - nothing to do (no non-" + LANGS + " tracks found)\n"
            continue

        # we don't need to process this since there's only a single track of each
        # and we don't want to be left without audio/subtitles
        if sum(tracks["audio"].values()) == 1 and sum(tracks["subtitles"].values()) == 1:
            print >> sys.stderr, " - nothing to do (only 1 audio & subtitle track)\n"
            continue

        # build command line to process the file
        cmd = [MKVMERGE, "-a", LANGS, "-s", LANGS, "-o", path + ".temp", path]

        # process file
        print >> sys.stderr, " - Processing", path, "...\n",
        mkvmerge = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = mkvmerge.communicate()
        if mkvmerge.returncode != 0:
            print >> sys.stderr, "  -- Failed\n"
            continue

        print >> sys.stderr, "  -- Succeeded\n"

        # overwrite file
        if KEEP:
            os.rename(path, path + ".original")
	    else:
            os.remove(path)
        os.rename(path + ".temp", path)
