import argparse
import glob
import fnmatch
import os
import subprocess
from colors import color
from tabulate import tabulate

#set command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--container', action='store_true', help='where possible only change container')
parser.add_argument('-o', '--optimize', action='store_true', help='optimize mp4 files for streaming')
parser.add_argument('-t', '--transcode', action='store_true', help='transcode files to mp4 with h264 and aac')
parser.add_argument('-l', '--list', action='store_true', help='list files that will be processed')
parser.add_argument('-d', '--data', action='store_true', help='list files that with codec data')
args = parser.parse_args()
 
# walk through directorys recursivley and get list of files
def get_files():
    fileList = []
    currentdir = os.getcwd()
    extentions = ['*.mp4', '*.mkv', '*.avi']
    for root, dirnames, filenames in os.walk(currentdir):
        for extension in extentions:
            for filename in fnmatch.filter(filenames, extension):
                fileList.append(os.path.join(root, filename))
    return fileList

#use ffprobe to get the codec data for each file and store in an list of dict    
def get_data(fileList):
    print('getting codec data this might take a while...') 
    fileData = []
    for file in fileList:
        print('processing: ' + file)
        try:
            values = {}
            acodec = (subprocess.check_output('ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
            vcodec = (subprocess.check_output('ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
            values['path'] = file
            values['vcodec'] = vcodec.strip()
            values['acodec'] = acodec.strip()
            fileData.append(values)            
        except:
            values = {}
            values['path'] = file
            values['vcodec'] = " "
            values['acodec'] = " "
            print('could not get file data')
    return fileData

#check the file extension, return true if mp4
def check_mp4(item):
    print('checking if mp4...')
    if(item['path'][-3:] == 'mp4'):
        print(color('file is mp4', fg='green'))
        return True
    else:
        print(color('file is not mp4', fg='red'))

#check the codecs, return true if h264 and aac/mp3
def check_codecs(item):
    print('checking if needs transcoding...')
    if((item['vcodec'] == 'h264') and (item['acodec'] == 'mp3' or item['acodec'] == 'aac')):
        print(color('file is transcoded using h264 and aac/mp3', fg='green'))
        return True
    else:
        print(color('file requires transcoding', fg='red'))

#check the moov atom using qtfaststart, return true if file is web optimized        
def check_optimized(item):
    print('checking if optimized...')
    try:
        optimized = subprocess.check_output('C:\Python27\python.exe -m qtfaststart -l "' + item['path'] + '"').splitlines()[1][0:4]
    except:
        optimized = " "
        print('could not get optimized status')
    if(optimized == "moov"):
        print(color('file is optimized', fg='green'))
        return True
    else:
        print(color('file is not optimized', fg='red'))

#print a list of file names        
if args.list:
    print('args list')
    for item in get_files():
        print(item)

#print a table of file names with codec data     
if args.data:
    print('args data')
    print tabulate(get_data(get_files()))

#check if mp4 and if not check the codes, if they are compliant, copy the streams
if args.container:
    print('arg container')
    for item in get_data(get_files()):
        #check not already mp4
        if not(check_mp4(item)):
            #check codecs are h264 and aac/mp3
            if(check_codecs(item)):
                #generate temp file name
                tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
                #generate new file name
                newfile = item['path'][:-4] + '.mp4'
                #rename the origional file with _temp
                os.rename(item['path'], tempfile)
                #change the container, copy the streams
                try:
                    subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v copy -c:a copy -movflags faststart "' + newfile + '"')
                except: 
                    print(color('could not change container', fg='red'))
                if os.path.isfile(newfile):
                    try:
                        os.remove(tempfile)
                    except:
                        continue
                else:
                    os.rename(tempfile, item['path'])

#check the moov atom of mpv files to ensire it is at the start of the file for quick streaming
if args.optimize:
    print('args optimize')
    for item in get_data(get_files()):
        #check if mp4
        if(check_mp4(item)):
            #check if not alreay optimized
            if not (check_optimized(item)):
                #generate temp file name
                tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
                #generate new file name
                newfile = item['path'][:-4] + '.mp4'
                #rename the origional file with _temp
                os.rename(item['path'], tempfile)
                #copy the streams and move the moov atom 
                try:
                    subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v copy -c:a copy -movflags faststart "' + newfile + '"')
                except: 
                    print(color('could not optimize file', fg='red'))
                #if new file exists delete the temp file
                if os.path.isfile(newfile):
                    try:
                        os.remove(tempfile)
                    except:
                        continue
                else:
                    os.rename(tempfile, item['path'])

#check if file needs transcoding, if it does, transcode, otherwise, copy the streams                    
if args.transcode:
    print('arg transcode')
    for item in get_data(get_files()):
        #if item is already mp4 and correctly transcoded, skip to next file
        if (check_mp4(item) and check_codecs(item)):
            continue
        else:
            #generate temp file name
            tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
            #generate new file name
            newfile = item['path'][:-4] + '.mp4'
            #rename the origional file with _temp
            os.rename(item['path'], tempfile)
            #check the video coded and copy the stream if h264
            if(item['vcodec'] == 'h264'):
                vcodec = 'copy'
            else:
                vcodec = 'h264'
            #check the audio stream and copy the stream if aac/mp3
            if(item['acodec'] == 'mp3' or item['acodec'] == 'aac'):
                acodec = 'copy'
            else:
                acodec = 'aac'
            #transcode the file
            try:
                subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v ' + vcodec + ' -c:a ' + acodec + ' -preset veryfast -movflags faststart -r 24 "' + newfile + '"')
            except: 
                print(color('could not transcode file', fg='red'))
            #if new file exists delete the temp file
            if os.path.isfile(newfile):
                try:
                    os.remove(tempfile)
                except:
                    continue
            #if new file doesn't exist put back the old file
            else:
                os.rename(tempfile, item['path'])
            

