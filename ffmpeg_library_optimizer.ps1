param (
    [switch]$list = $false,
    [switch]$container = $false,
    [switch]$transcode = $false,
    [switch]$optimize =$false,
    [switch]$convert =$false
)

#get all files in the directory recirsivley with included extensions
$file_names = Get-Childitem -File -Include *.mkv, *avi, *.mp4 -Recurse


Write-Host Processing $file_names.Count Files -foregroundcolor "Magenta"
#iterate over the files and get the audio and video codecs
if ($list) {
    #create a powershell array
    $file_info = @()
    
    Write-Host "Generating list, this might take a while..."
    
    for ($i=0; $i -lt $file_names.Count; $i++){
        #get the video codec 
        $video_codec = C:\tools\ffmpeg-3.4.1\bin\ffprobe.exe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 $file_names[$i].FullName
        #get the audio codec 
        $audio_codec = C:\tools\ffmpeg-3.4.1\bin\ffprobe.exe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 $file_names[$i].FullName
        #add the properties to a powershell object 
        $file = New-Object -TypeName PSObject
        $file | Add-Member -Type NoteProperty -Name "Full Name" -Value $file_names[$i].FullName
        $file | Add-Member -Type NoteProperty -Name "Name" -Value $file_names[$i].Basename
        $file | Add-Member -Type NoteProperty -Name "Extension" -Value $file_names[$i].Extension
        $file | Add-Member -Type NoteProperty -Name "Video Codec" -Value $video_codec
        $file | Add-Member -Type NoteProperty -Name "Audio Codec" -Value $audio_codec
        #add each ojject to the array
        $file_info += $file
    }
    Write-Host ($file_info | Format-Table -Property @{e='Name'; width =60 }, @{e='Extension'; width =10 }, @{e='Audio Codec'; width =10 }, @{e='Video Codec'; width =10 } | Out-String) 
}

if ($container -or $transcode){
    for ($i=0; $i -lt $file_names.Count; $i++){
        #get the fiel name
        $file_name = $file_names[$i].FullName
        
        Write-Host Processing $file_name -foregroundcolor "Green"
        
        #get the video codec
        $video_codec = C:\tools\ffmpeg-3.4.1\bin\ffprobe.exe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 $file_name
        #get the audio codec 
        $audio_codec = C:\tools\ffmpeg-3.4.1\bin\ffprobe.exe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 $file_name
        #get the conatiner
        $file_conatiner = $file_name.Substring($file_name.length - 3,3)
        
        #copy the video stream, don't transcode if it is already h264
        if (($video_codec -eq "h264")){
            $video_codec_out = "copy"
        }
        else{
            $video_codec_out = "libx264"
        }
     
        #copy the audio stream, don't transcode if it is already aac or mp3
        if (($audio_codec -eq "aac") -or ($audio_codec -eq "mp3")){
            $audio_codec_out = "copy"
        }
        else{
            $audio_codec_out = "aac"
        }
        
        #continue if conversion is not needed
        if (($video_codec_out -eq "copy") -and ($audio_codec_out -eq "copy") -and ($file_conatiner -eq "mp4")){
            Write-Host "No conversion needed for:" $file_name -foregroundcolor "Green"
            Continue
        }
        
        #generate the temp file name
        $temp_file_name = $file_names[$i].DirectoryName + "\" + $file_names[$i].BaseName + "_temp" + $file_names[$i].Extension
        
        #generate name for the new file
        $new_file_name = [io.path]::ChangeExtension($file_name, '.mp4')
        
        $argument_list = "-loglevel info -y -i """ + $temp_file_name + """ -c:v " + $video_codec_out + " -c:a " + $audio_codec_out + " -preset veryfast -movflags faststart -r 24 """ + $new_file_name + """ -hide_banner"
        
        #if container flag is set dont transcode only change containers
        if ($container) {
            #check if the file needs transcoding
            if (($video_codec_out -eq "copy") -and ($audio_codec_out -eq "copy")) {
                #rename the origial file to temp file
                Rename-Item -Path $file_name -NewName $temp_file_name
                #start ffmpeg
                Start-Process -FilePath C:\tools\ffmpeg-3.4.1\bin\ffmpeg.exe $argument_list -Wait -NoNewWindow
                if (Test-Path $new_file_name){
                    #remove the old file
                    Remove-Item $temp_file_name
                    Write-Host Completed: $file_names[$i].Name -foregroundcolor "Green"
                }
                else {
                    #put back the old file if optimisation couldn't be completed
                    Rename-Item -Path $temp_file_name -NewName $file_name
                    Write-Host Failed: $file_names[$i].Name -foregroundcolor "Red"
                }
            }
            else{
                Write-Host This file requires transcoding -foregroundcolor "Red"
            }
        }
        
        #if the transcode flag is set then transcode files where a container change is not sufficient
        if ($transcode) {
            #rename the origial file to temp file
            Rename-Item -Path $file_name -NewName $temp_file_name    
            #start ffmpeg
            Start-Process -FilePath C:\tools\ffmpeg-3.4.1\bin\ffmpeg.exe $argument_list -Wait -NoNewWindow
            if (Test-Path $new_file_name){
                #remove the old file
                Remove-Item $temp_file_name
                Write-Host Completed: $file_names[$i].Name -foregroundcolor "Green"
            }
            else {
                #put back the old file if optimisation couldn't be completed
                Rename-Item -Path $temp_file_name -NewName $file_name
                Write-Host Failed: $file_names[$i].Name -foregroundcolor "Red"
            }
        }
    }
}
if ($optimize){
    for ($i=0; $i -lt $file_names.Count; $i++){
        Write-Host "Optimizing File:" $file_names[$i].Name -foregroundcolor "Green"
        #set temp file name
        $file_name = $file_names[$i].FullName
        if ($file_name.Substring($file_name.length - 3,3) -ne "mp4"){
            Write-Host "not mp4"
            Continue
        }
        Try{
            $optimized = (C:\Python27\python.exe -m qtfaststart -l $file_name)[1].StartsWith("moov")
        }
        Catch {
            Write-Host "cannot get moov atom"
        }     
        if ($optimized){
            Write-Host $file_names[$i].Name is already optimized -foregroundcolor "Yellow"
            Continue
        }
        $temp_file_name = $file_names[$i].DirectoryName + "\" + $file_names[$i].BaseName + "_temp" + $file_names[$i].Extension
        #move file to a temp file
        Rename-Item -Path $file_name -NewName $temp_file_name
        #set arguments
        $argument_list = "-loglevel fatal -y -i """ + $temp_file_name + """ -c:v copy -c:a copy -movflags faststart """ + $file_name + """ -hide_banner"
        #start ffmpeg
        Start-Process -FilePath C:\tools\ffmpeg-3.4.1\bin\ffmpeg.exe $argument_list -Wait -NoNewWindow
        #check optimisation was completed
        if (Test-Path $file_name){
            #remove the old file
            Remove-Item $temp_file_name
            Write-Host Optimized File: $file_names[$i].Name -foregroundcolor "Green"
        }
        else {
            #put back the old file if optimisation couldn't be completed
            Rename-Item -Path $temp_file_name -NewName $file_name
            Write-Host Failed to Optimize: $file_names[$i].Name -foregroundcolor "Red"
        }
    }
}