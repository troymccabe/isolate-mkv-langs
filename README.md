# isolate-mkv-langs
Use MKVMerge to strip all but specified languages from your .mkvs. [USE AT YOUR OWN RISK]

## USE AT YOUR OWN RISK
This worked for my files, but I obviously couldn't test this on yours. Using this script is at your own risk, and I assume no responsibility for lost/damaged files

## Usage
1. Download the repo (or just grab `isolate_mkv_langs.py`)
2. From command line: `py isolate_mkv_langs.py -d /path/to/mkvs -l 3-char_lang_code -m /path/to/mkvmerge`

## Help
```
isolate_mkv_langs.py -d </path/to/mkvs> -l <3-char_lang_code> -m </path/to/mkvmerge>
                  
 Options:
  -d, --dir <folder>            The directory where your MKVs are stored
  -h, --help                    Display help text
  -k, --keep        	        Keep original file
  -l, --langs <languages>       3-character language code (e.g. eng). To retain multiple, separate languages with a comma (e.g. eng,spa)
  -m, --mkvmerge <executable>   The path to the MKVMerge executable
```
