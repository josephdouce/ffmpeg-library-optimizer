import argparse
import glob
import fnmatch
import os
import subprocess
from tabulate import tabulate

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--container', action='store_true', help='where possible only change container')
parser.add_argument('-o', '--optimize', action='store_true', help='optimize mp4 files for streaming')
parser.add_argument('-t', '--transcode', action='store_true', help='transcode files to mp4 with h264 and aac')
parser.add_argument('-l', '--list', action='store_true', help='list files that will be processed')
parser.add_argument('-d', '--data', action='store_true', help='list files that with codec data')
args = parser.parse_args()
 
# Walk through directory
def get_files():
    fileList = []
    currentdir = os.getcwd()
    extentions = ['*.mp4', '*.mkv', '*.avi']
    for root, dirnames, filenames in os.walk(currentdir):
        for extension in extentions:
            for filename in fnmatch.filter(filenames, extension):
                fileList.append(os.path.join(root, filename))
    return fileList
  
def get_data(fileList):
    print('getting codec data this might take a while...') 
    fileData = []
    for file in fileList:
        values = {}
        acodec = (subprocess.check_output('ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
        vcodec = (subprocess.check_output('ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
        values['path'] = file
        values['vcodec'] = vcodec.strip()
        values['acodec'] = acodec.strip()
        fileData.append(values) 
    return fileData

def check_mp4(item):
    print('checking if mp4')
    if(item['path'][-3:] == 'mp4'):
        print('file is mp4')
        return True
    else:
        print('file is not mp4')

def check_codecs(item):
    print('checking if needs transcoding')
    if(item['vcodec'] == 'h264' and item['acodec'] == 'mp3' or item['acodec'] == 'aac'):
        print('file does not require transcoding')
        return True
    else:
        print('file requires transcoding')
 
def check_optimized(item):
    print('checking if optimized')
    optimized = subprocess.check_output('C:\Python27\python.exe -m qtfaststart -l "' + item['path'] + '"').splitlines()[1][0:4]
    if(optimized == "moov"):
        print('file is already optimized')
        return True
    else:
        print('file is not optimized')
        
if args.list:
    print('args list')
    for item in get_files():
        print(item)
    
if args.data:
    print('args data')
    print tabulate(get_data(get_files()))

if args.optimize:
    print('args optimize')
    for item in get_data(get_files()):
        #make sure the file is an mp4
        if(check_mp4(item)):
            if not (check_optimized(item)):
                tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
                os.rename(item['path'], tempfile)
                try:
                    subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v copy -c:a copy -movflags faststart "' + item['path'] + '"')
                except: 
                    print('could not optimize file')
                if os.path.isfile(item['path']):
                    os.remove(tempfile)
                else:
                    os.rename(tempfile, item['path'])

if args.container:
    print('arg container')
    for item in get_data(get_files()):
        #make sure the file is not an mp4
        if not(check_mp4(item)):
            if(check_codecs(item)):   
                tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
                os.rename(item['path'], tempfile)
                try:
                    subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v copy -c:a copy -movflags faststart "' + item['path'][:-4] + '.mp4"')
                except: 
                    print('could not change container')
                if os.path.isfile(item['path']):
                    os.remove(tempfile)
                else:
                    os.rename(tempfile, item['path'])

if args.transcode:
    print('arg transcode')
    for item in get_data(get_files()):
        if not (check_codecs(item)):
            tempfile = item['path'][:-4] + "_temp" + item['path'][-4:]
            os.rename(item['path'], tempfile)
            try:
                subprocess.check_output('ffmpeg -loglevel info -y -i "' + tempfile + '" -c:v h264 -c:a aac -preset veryfast -movflags faststart -r 24 "' + item['path'][:-4] + '.mp4"')
            except: 
                print('could not transcode file')
            if os.path.isfile(item['path']):
                os.remove(tempfile)
            else:
                os.rename(tempfile, item['path'])
            

