 param (
    [switch]$list = $false,
    [switch]$container = $false,
    [switch]$transcode = $false
 )

#get all files in the directory recirsivley with included extensions
$file_names = Get-Childitem -File -Include *.mkv, *avi -Recurse

#create a powershell array
$file_info = @()

#iterate over the files and get the audio and video codecs
for ($i=0; $i -lt $file_names.Count; $i++){
    Write-Host "Processing:" $file_names[$i].Name
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

if ($list) {
    Write-Host ($file_info | Format-Table -Property @{e='Name'; width =60 }, @{e='Extension'; width =10 }, @{e='Audio Codec'; width =10 }, @{e='Video Codec'; width =10 } | Out-String) 
}

#itterate through the array of files 
foreach ($file in $file_info){

    $video_codec_out = "libx264"
    $audio_codec_out = "aac"
    
    #copy the video stream, don't transcode if it is already h264
    if ($file."Video Codec" -eq "h264"){
        $video_codec_out = "copy"
    }
    
    #copy the audio stream, don't transcode if it is already aac or mp3
    if ($file."Audio Codec" -eq "aac" -or $file."Audio Codec" -eq "mp3"){
        $audio_codec_out = "copy"
    }
   
    $new_file_name = [io.path]::ChangeExtension($file."Full Name", '.mp4')
    $argument_list = " -i """ + $file."Full Name" + """ -c:v " + $video_codec_out + " -c:a " + $audio_codec_out + " """ + $new_file_name + """ -hide_banner"
    
    #if container flag is set dont transcode only change containers
    if ($container) {
        #check if the file needs transcoding
        if (($video_codec_out -eq "copy") -and ($audio_codec_out -eq "copy")) {
            #start ffmpeg1q
            Start-Process -FilePath C:\tools\ffmpeg-3.4.1\bin\ffmpeg.exe $argument_list -Wait -NoNewWindow
            #delete origional
            Remove-Item $file."Full Name"
        }
    }
    
    #if the transcode flag is set then transcode files where a container change is not sufficient
    if ($transcode) {
        #start ffmpeg
        Start-Process -FilePath C:\tools\ffmpeg-3.4.1\bin\ffmpeg.exe $argument_list -Wait -NoNewWindow
        #delete origional
        Remove-Item $file."Full Name"
    }
}