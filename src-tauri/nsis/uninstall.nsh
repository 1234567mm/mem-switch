; Mem-Switch NSIS Uninstall Script Customization
; This ensures clean uninstallation with no残留

; Remove user data option
!ifndef NO_REMOVE_USER_DATA
  Var /GLOBAL REMOVE_USER_DATA
!endif

; Clean uninstall section
Section "Uninstall"
  ; Remove installed files
  RMDir /r "$INSTDIR"

  ; Remove desktop shortcut
  Delete "$DESKTOP\Mem-Switch.lnk"

  ; Remove start menu shortcut
  Delete "$SMPROGRAMS\Mem-Switch.lnk"
  RMDir "$SMPROGRAMS\Mem-Switch"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mem-Switch"
  DeleteRegKey HKCU "Software\Mem-Switch"

  ; Optional: Remove user data (if checkbox selected)
  !ifndef NO_REMOVE_USER_DATA
    ${If} $REMOVE_USER_DATA == 1
      RMDir /r "$LOCALAPPDATA\mem-switch"
      RMDir /r "$APPDATA\mem-switch"
    ${EndIf}
  !endif

  ; Clean uninstall complete
  MessageBox MB_OK "Mem-Switch has been uninstalled.$\n$\nUser data was $(if $REMOVE_USER_DATA == 1 then 'removed' else 'preserved')."
SectionEnd

; Custom page for data removal option
!ifndef NO_REMOVE_USER_DATA
  Function .onVerifyInstDir
    ; Validate installation directory
    StrCmp "$INSTDIR" "" 0 +2
      Abort "Installation directory cannot be empty"
  FunctionEnd

  Function un.onInit
    ; Initialize data removal option
    StrCpy $REMOVE_USER_DATA 0
  FunctionEnd

  !define MUI_FINISHPAGE_TEXT "Also remove user data and configuration files?"
  !define MUI_FINISHPAGE_RUN "$INSTDIR\mem-switch.exe"
!endif
