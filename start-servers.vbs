' Fastline Ordering Server Launcher (VBScript)
' This creates an executable-like experience

Dim objShell, objFSO
Dim scriptDir, flaskDir, nextjsDir
Dim result

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
flaskDir = scriptDir & "\flask_app"
nextjsDir = scriptDir & "\ghl-custom-frontend"

' Check if directories exist
If Not objFSO.FolderExists(flaskDir) Then
    MsgBox "Error: Flask directory not found at " & flaskDir, vbCritical, "Fastline Ordering Launcher"
    WScript.Quit 1
End If

If Not objFSO.FolderExists(nextjsDir) Then
    MsgBox "Error: Next.js directory not found at " & nextjsDir, vbCritical, "Fastline Ordering Launcher"
    WScript.Quit 1
End If

' Ask user if they want to start the servers
result = MsgBox("Start Fastline Ordering servers?" & vbCrLf & vbCrLf & _
                "Flask API: http://localhost:5000" & vbCrLf & _
                "Next.js App: http://localhost:3000", _
                vbYesNo + vbQuestion, "Fastline Ordering Launcher")

If result = vbYes Then
    ' Start Flask server
    objShell.Run "cmd /k ""cd /d """ & flaskDir & """ && title Flask API Server - Port 5000 && python app_orders.py""", 1, False
    
    ' Wait a moment
    WScript.Sleep 2000
    
    ' Start Next.js server  
    objShell.Run "cmd /k ""cd /d """ & nextjsDir & """ && title Next.js Frontend - Port 3000 && npm run dev""", 1, False
    
    ' Show success message
    MsgBox "Servers are starting!" & vbCrLf & vbCrLf & _
           "Flask API: http://localhost:5000" & vbCrLf & _
           "Next.js App: http://localhost:3000" & vbCrLf & vbCrLf & _
           "Close the command windows to stop the servers.", _
           vbInformation, "Fastline Ordering Launcher"
End If

' Clean up
Set objShell = Nothing
Set objFSO = Nothing