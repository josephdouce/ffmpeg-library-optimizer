# ffmpeg-library-optimizer
optimize/transcode media library using ffmpeg

usage 

pip install -r requiremnts.txt
cd to your media directory
ffmpeg-library-optimizer.py -h

-h, --help          shows options 
-l, --list          list all files to be processed
-d, --data          list files and there codecs
-o, --optimize      files this will only copy streams and move the moov atom to enable fast web playback, files that require transcoding will be skipped
-t, --transcode     this will transcode all files that are not mp4 with h264 and aac/mp3 then optimize them

