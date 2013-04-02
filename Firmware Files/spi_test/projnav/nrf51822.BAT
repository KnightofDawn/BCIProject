SET PATH=C:\Program Files\Keil\ARM\ARMCC\bin\;C:\Program Files (x86)\AMD APP\bin\x86_64;C:\Program Files (x86)\AMD APP\bin\x86;C:\Program Files\Common Files\Microsoft Shared\Windows Live;C:\Program Files (x86)\Common Files\Microsoft Shared\Windows Live;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\;C:\Program Files (x86)\ATI Technologies\ATI.ACE\Core-Static;C:\Program Files (x86)\Windows Live\Shared;C:\Program Files\MATLAB\R2009b\runtime\win64;C:\Program Files\MATLAB\R2009b\bin;C:\Program Files (x86)\Nordic Semiconductor\nrf51\bin\;
SET CPU_TYPE=nRF51822
SET CPU_VENDOR=Nordic
SET UV2_TARGET=nrf51822
SET CPU_CLOCK=0x00F42400
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "main._1i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "system_nrf51._1i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmAsm" --Via ".\arm_startup_nrf51._ia"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "spi_master._1i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "nrf_delay._1i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmLink" --Via "spi_test.l1p"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "main._2i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "system_nrf51._2i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmAsm" --Via ".\arm_startup_nrf51._ia"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "spi_master._2i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmCC" --Via "nrf_delay._2i"
"C:\Program Files\Keil\ARM\ARMCC\bin\ArmLink" --Via "spi_test.l2p"
C:\Program Files\Keil\ARM\ARMCC\bin\fromelf.exe "spi_test.axf" --i32combined --output "spi_test.hex"
