$scriptpath = '#####client.ps1'

$trigger = New-JobTrigger -AtStartup -RandomDelay 00:00:30
Register-ScheduledJob -Trigger $trigger -FilePath $scriptpath -Name AwiDomClientStartUP
