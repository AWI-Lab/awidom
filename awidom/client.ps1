function Build-Command-Watcher([String] $Path) {
  <#Build and execute the watcher for a command file.

  Args:
    Path (String): The path to the command YAML file
  #>
  $Path = Normalize-Path -Path $Path
  $Folder = Split-Path -Path $Path
  $Filename = Split-Path -Path $Path -leaf
  $Watcher = New-Object IO.FileSystemWatcher $Folder, $Filename -Property @{
    IncludeSubdirectories = $false
    NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
  }
  $global:CheckCommandFile = $true
  try{
    Unregister-Event CommandFileChanged
  }catch{$false}
  Write-Host "Registering onCommandChange"
  $OnCommandChange = Register-ObjectEvent $Watcher Changed -SourceIdentifier CommandFileChanged -Action {
    Write-Host "Triggerd onCommandChange"
    if ($global:CheckCommandFile -eq 1) {
      Write-Host "is valid"
      $global:CheckCommandFile = $false
      $Path = $Event.SourceEventArgs.FullPath
      $Name = $Event.SourceEventArgs.Name

      # Get a new command and execute:
      $Command = Get-OwnCommand -Path $Path -Attr $env:COMPUTERNAME
      $Exec, $Args = Split-ArgumentCommandPath -Command $Command
      if ($Command -ne '') {
        Write-Host "$Exec with Args: $Args"
        & $Exec $Args
      }

      # Pause the FileSystemWatcher for 10sec:
      Write-Host "Started timer"
      Start-Sleep -s 1
      Write-Host "Ended timer"
      $global:CheckCommandFile = $true
    }
  }
}


function Split-ArgumentCommandPath([String] $Command) {
  <#Fetch the arguments from an command string.

  Args:
    Command (String): The command string

  Returns:
    the retrieved arguments
  #>
  $RegEx = "(.*?)( [-|\\].*|$)"
  $matched = $Command -match $RegEx
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


function Get-FromYAML($Text, [String] $Attr) {
  <#Get a value for a key in an YAML text.

  Args:
    Text (String): The YAML text
    Attr (String): The key

  Returns:
    the value or ''
  #>
  $Line = $Text | Select-String -Pattern ($Attr)
  Write-Host $Line
  if ($Line -match ".*'(?<content>.*)'.*" -eq 1) {
    return $matches['content']
  }else{
    return ''
  }
}


function Get-OwnCommand([String] $Path, [String] $Attr) {
  <#Get the new command from YAML file and delete it

  Args:
    Path (String): The path to the YAML file
    Attr (String): The ID to look for in the YAML file

  Returns:
    the new command or ''
  #>
  $Path = Normalize-Path -Path $Path
  $Content = Get-Content $Path
  $Command = Get-FromYAML -Text $Content -Attr $Attr

  if ($Command -eq '') {
    return ''
  }

  while ($true) {
    try{
      $File = New-Object IO.FileStream($Path, 'Truncate', 'Write', 'None')
      $NewContent = $Content | Where-Object {$_ -notmatch $Attr}
      $NewContent = ($NewContent -join "`r`n")
      $Writer = New-Object System.IO.StreamWriter($File)
      $Writer.Write($NewContent)
      $Writer.Dispose()
      $File.Dispose()
      break
    }
    catch{
      Start-Sleep -m 100
    }
  }

  return $Command
}
