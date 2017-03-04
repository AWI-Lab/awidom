function Build-Command-Watcher([String] $Path) {
  $Path = Normalize-Path -Path $Path
  $folder = Split-Path -Path $Path
  $filename = Split-Path -Path $Path -leaf
  $Watcher = New-Object IO.FileSystemWatcher $folder, $filename -Property @{
    IncludeSubdirectories = $false
    NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
  }
  try{
    Unregister-Event -SourceIdentifier "CommandFileChanged"
  }catch{$false}
  $onCommandChange = Register-ObjectEvent $Watcher Changed -SourceIdentifier CommandFileChanged -Action {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $command = Get-Own-Command -Path $path -Attr $env:COMPUTERNAME
    if ($command -ne '') {
      Write-Host "$command"
      & $command
    }
  }
}

function Get-Arguments-From-Command([String] $command) {
  $command -match ".*\\.*? (.*)"
  return $matc
}

function Normalize-Path([String] $Path) {
  if ([System.IO.Path]::IsPathRooted($Path) -eq 1) {
    return $Path
  }else{
    return [System.IO.Path]::GetFullPath((Join-Path (pwd) $Path))
  }
}

function Get-From-YAML([String] $Text, [String] $Attr) {
  $line = $Text | Select-String -Pattern ($Attr)
  if ($line -match ".*'(?<content>.*)'.*" -eq 1) {
    return $matches['content']
  }else{
    return ''
  }
}

function Get-Own-Command([String] $Path, [String] $Attr) {
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
