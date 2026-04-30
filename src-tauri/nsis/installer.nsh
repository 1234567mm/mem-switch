; Mem-Switch NSIS Installer Configuration
; Custom installer settings for Windows

; Installation mode: allow both perUser and perMachine
!macro customInstallMode
  ; Allow user to choose installation mode
  InstallMode "both"
!macroend

; Installer icon
!define NSIS_INSTALLER_ICON "icons/icon.ico"

; Display language selector
!define NSIS_LANGUAGES "SimpChinese,English"
!define NSIS_DISPLAY_LANGUAGE_SELECTOR true

; Allow custom installation directory
!define NSIS_ONE_CLICK false
!define NSIS_ALLOW_CUSTOM_DIRECTORY true

; Uninstall display name
!define NSIS_UNINSTALL_DISPLAY_NAME "Mem-Switch"

; Custom install page text
!define MUI_WELCOMEPAGE_TITLE "欢迎安装 Mem-Switch"
!define MUI_WELCOMEPAGE_TEXT "本向导将引导您完成 Mem-Switch 的安装。$\r$\n$\r$\n建议关闭其他正在运行的程序，以确保安装过程顺利。"

; Custom finish page text
!define MUI_FINISHPAGE_TITLE "Mem-Switch 安装完成"
!define MUI_FINISHPAGE_TEXT "Mem-Switch 已成功安装到您的计算机。$\r$\n$\r$\n点击\"完成\"启动 Mem-Switch。"

; Custom uninstall page
!define MUI_UNWELCOMEPAGE_TITLE "卸载 Mem-Switch"
!define MUI_UNWELCOMEPAGE_TEXT "本向导将引导您卸载 Mem-Switch。$\r$\n$\r$\n卸载前，建议备份您的数据。"
