function Build-Command-Watcher([String] $Path) {
  <#Build and execute the watcher for a command file.

  Args:
    Path (String): The path to the command YAML file
  #>
  $Path = Normalize-Path -Path $Path
  $folder = Split-Path -Path $Path
  $filename = Split-Path -Path $Path -leaf
  $Watcher = New-Object IO.FileSystemWatcher $folder, $filename -Property @{
    IncludeSubdirectories = $false
    NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
  }
  try{
    Unregister-Event CommandFileChanged
  }catch{$false}
  $onCommandChange = Register-ObjectEvent $Watcher Changed -SourceIdentifier CommandFileChanged -Action {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name

    # Pause the FileSystemWatcher for 10sec:
    $watcher.EnableRaisingEvents = $false
    $EventTimer = New-Object timers.timer
    $EventTimer.Interval = 10000
    $action = {
      $watcher.EnableRaisingEvents = $true
      Unregister-Event RaisingTimer
    }
    Register-ObjectEvent -InputObject $EventTimer -EventName elapsed -SourceIdentifier RaisingTimer -Action $action
    $EventTimer.Start()

    # Get a new command and execute:
    $command = Get-Own-Command -Path $path -Attr $env:COMPUTERNAME
    $exec, $args = Split-Argument-Command-Path -Command $command
    if ($command -ne '') {
      Write-Host "$exec with Args: $args"
      & $exec $args
    }

  }
}


function Split-Argument-Command-Path([String] $Command) {
  <#Fetch the arguments from an command string.

  Args:
    Command (String): The command string

  Returns:
    the retrieved arguments
  #>
  $regex = "(.*?)( [-|\].*|$)"
  $matched = $Command -match $regex
  return $matches[1].Trim().Split(), $matches[2].Trim().Split()
}


function Normalize-Path([String] $Path) {
  <#Normalize a file path.

  Args:
    Path (String): The path to normalize

  Returns:
    the normalized path
  #>
  if ([System.IO.Path]::IsPathRooted($Path) -eq 1) {
    return $Path
  }else{
    return [System.IO.Path]::GetFullPath((Join-Path (pwd) $Path))
  }
}


function Get-From-YAML([String] $Text, [String] $Attr) {
  <#Get a value for a key in an YAML text.

  Args:
    Text (String): The YAML text
    Attr (String): The key

  Returns:
    the value or ''
  #>
  $line = $Text | Select-String -Pattern ($Attr)
  if ($line -match ".*'(?<content>.*)'.*" -eq 1) {
    return $matches['content']
  }else{
    return ''
  }
}


function Get-Own-Command([String] $Path, [String] $Attr) {
  <#Get the new command from YAML file and delete it

  Args:
    Path (String): The path to the YAML file
    Attr (String): The ID to look for in the YAML file

  Returns:
    the new command or ''
  #>
  $Path = Normalize-Path -Path $Path
  $content = Get-Content $Path
  $command = Get-From-YAML -Text $content -Attr $Attr

  if ($command -eq '') {
    return ''
  }

  while ($true) {
    try{
      $file = [System.io.File]::Open($Path, 'Open', 'Write', 'Read')
      $newcontent = Get-Content $Path | Where-Object {$_ -notmatch $Attr}
      $writer = New-Object System.IO.StreamWriter($file)
      $writer.Write(($newcontent -join "`r`n"))
      $writer.Close()
      $file.Close()
      break
    }
    catch{
      Start-Sleep -m 100
    }
  }

  return $command
}
