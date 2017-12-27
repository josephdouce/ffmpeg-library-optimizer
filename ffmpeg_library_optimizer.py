import argparse
import glob
import fnmatch
import os
import subprocess
import time
from colors import color
from tabulate import tabulate
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Optimizer:

    # walk through directorys recursivley and get list of files
    def get_files(self):
        fileList = []
        currentdir = os.getcwd()
        extentions = ['*.mp4', '*.mkv', '*.avi']
        for root, dirnames, filenames in os.walk(currentdir):
            for extension in extentions:
                for filename in fnmatch.filter(filenames, extension):
                    fileList.append(os.path.join(root, filename))
        return fileList
        
    #use ffprobe to get the codec data for each file and store in an list of dict    
    def get_data(self, file):
        print('processing file: ' + file)
        try:
            values = {}
            acodec = (subprocess.check_output('ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
            vcodec = (subprocess.check_output('ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "' + file + '"'))
            values['path'] = file
            values['vcodec'] = vcodec.strip()
            values['acodec'] = acodec.strip()           
        except:
            values = {}
            values['path'] = file                                                                                                                                        
            values['vcodec'] = ""
            values['acodec'] = ""
            print('could not get file data')
        return values

    #check the file extension, return true if mp4
    def check_mp4(self, file):
        if(file['path'][-3:] == 'mp4'):
            print(color('file is mp4', fg='green'))
            return True
        else:
            print(color('file is not mp4', fg='red'))

    #check the codecs, return true if h264 and aac/mp3
    def check_codecs(self, file):
        if((file['vcodec'] == 'h264') and (file['acodec'] == 'mp3' or file['acodec'] == 'aac')):
            print(color('file is transcoded using h264 and aac/mp3', fg='green'))
            return True
        else:
            print(color('file requires transcoding', fg='red'))

    #check the moov atom using qtfaststart, return true if file is web optimized        
    def check_optimized(self, file):
        try:
            optimized = subprocess.check_output('C:\Python27\python.exe -m qtfaststart -l "' + file['path'] + '"').splitlines()[1][0:4]
        except:
            optimized = " "
            print('could not get optimized status')
        if(optimized == "moov"):
            print(color('file is optimized', fg='green'))
            return True
        else:
            print(color('file is not optimized', fg='red'))

    #print a list of file names 
    def list(self):
        for file in self.get_files():
            print(file)

    #print a table of file names with codec data         
    def data(self):
        fileData = []
        for file in self.get_files():
            fileData.append(self.get_data(file))
        print tabulate(fileData)

    #check the moov atom of mpv files to ensure it is at the start of the file for quick streaming, also check container is mp4                   
    def optimize(self, file):
        #check file doesnt need transcode
        print('checking file: ' + file['path'])
        if(self.check_codecs(file)):
            #check if not optimized or not mp4
            if not (self.check_optimized(file) and self.check_mp4(file)):
                #generate temp file name
                tempfile = file['path'][:-4] + "_temp" + file['path'][-4:]
                #generate new file name
                newfile = file['path'][:-4] + '.mp4'
                #rename the origional file with _temp
                os.rename(file['path'], tempfile)
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
                        pass
                else:
                    os.rename(tempfile, file['path'])

    #check if file needs transcoding, if it does, transcode, otherwise, copy the streams                     
    def transcode(self, file):
        #if file is already mp4 and correctly transcoded, skip to next file
        print('checking file: ' + file['path'])
        if (self.check_codecs(file) and self.check_mp4(file) and self.check_optimized(file)):
            pass
        else:
            #generate temp file name
            tempfile = file['path'][:-4] + "_temp" + file['path'][-4:]
            #generate new file name
            newfile = file['path'][:-4] + '.mp4'
            #rename the origional file with _temp
            os.rename(file['path'], tempfile)
            #check the video coded and copy the stream if h264
            if(file['vcodec'] == 'h264'):
                vcodec = 'copy'
            else:
                vcodec = 'h264'
            #check the audio stream and copy the stream if aac/mp3
            if(file['acodec'] == 'mp3' or file['acodec'] == 'aac'):
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
                    pass
            #if new file doesn't exist put back the old file
            else:
                os.rename(tempfile, file['path'])        

class Watcher:

    DIRECTORY_TO_WATCH = os.getcwd()

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
            print "Watcher Stopped"
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print "Received created event - %s." % event.src_path

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print "Received modified event - %s." % event.src_path

if __name__ == '__main__':
    
    #command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--optimize', action='store_true', help='optimize files for web streaming, will only copy streams not transcode')
    parser.add_argument('-t', '--transcode', action='store_true', help='transcode files to mp4 with h264 and aac and optimize for web streaming')
    parser.add_argument('-l', '--list', action='store_true', help='list files that will be processed')
    parser.add_argument('-d', '--data', action='store_true', help='list files that with codec data')
    parser.add_argument('-w', '--watch', action='store_true', help='watch the directory for changes and transcode new files')
    args = parser.parse_args()

    optimize = Optimizer()
    files = optimize.get_files()
        
    if args.list:
        optimize.list()
      
    if args.data:
        optimize.data()

    if args.optimize:                             
        for file in files:
            optimize.optimize(optimize.get_data(file))
                                          
    if args.transcode:
        for file in files:
            optimize.transcode(optimize.get_data(file))

    if args.watch:
        w = Watcher()
        w.run()

            

