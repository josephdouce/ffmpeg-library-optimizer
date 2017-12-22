#get all files in the directory recirsivley with included extensions
$file_names = Get-Childitem -File -Include *.mp4 -Recurse
Write-Host Processing $file_names.Count Files -foregroundcolor "Magenta"
#iterate over the files and get the audio and video codecs
for ($i=0; $i -lt $file_names.Count; $i++){
    Write-Host "Optimizing File:" $file_names[$i].Name -foregroundcolor "Green"
    #set temp file name
    $file_name = $file_names[$i].FullName
    $optimized = (C:\Python27\python.exe -m qtfaststart -l $file_name)[1].StartsWith("moov")
    
    if ($optimized){
        Write-Host $file_names[$i].Name is already optimized -foregroundcolor "Yellow"
        Continue
    }
    $temp_file_name = $file_names[$i].DirectoryName + "\" + $file_names[$i].BaseName + "_temp" + $file_names[$i].Extension
    #move file to a temp file
    Rename-Item -Path $file_name -NewName $temp_file_name
    #set arguments
    $argument_list = "-loglevel fatal -i """ + $temp_file_name + """ -c:v copy -c:a copy -movflags faststart """ + $file_name + """ -hide_banner"
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
