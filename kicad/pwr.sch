EESchema Schematic File Version 2
LIBS:mmM
LIBS:power
LIBS:mmM-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 3 4
Title "uControl"
Date "1 jan 2014"
Rev "1"
Comp "WyoLum"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Wire Notes Line
	8275 2050 7175 2050
Wire Wire Line
	7325 1925 7925 1925
Wire Notes Line
	7175 3075 7875 3075
Wire Wire Line
	7625 3700 7625 3575
Wire Notes Line
	600  600  6725 600 
Wire Notes Line
	7175 3075 7175 4825
Wire Notes Line
	7875 3075 7875 4825
Wire Wire Line
	7625 4700 7400 4700
Wire Wire Line
	7625 4200 7625 4250
Wire Wire Line
	7625 3575 7400 3575
Wire Notes Line
	600  600  600  2850
Wire Wire Line
	7625 4700 7625 4650
Wire Wire Line
	7400 4700 7400 4750
Wire Notes Line
	6725 600  6725 2850
Wire Notes Line
	6725 2850 600  2850
Wire Notes Line
	8275 2050 8275 600 
Wire Wire Line
	7625 925  7625 875 
Wire Wire Line
	7325 1925 7325 1875
Wire Wire Line
	7625 1875 7625 1975
Wire Wire Line
	7325 1475 7325 1425
Wire Wire Line
	7625 1425 7625 1475
Connection ~ 7625 1925
Wire Wire Line
	7325 925  7325 875 
Wire Notes Line
	7175 2050 7175 600 
Wire Notes Line
	7875 4825 7175 4825
Wire Wire Line
	7925 1425 7925 1475
Wire Wire Line
	7925 1925 7925 1875
Wire Wire Line
	7925 925  7925 875 
Wire Notes Line
	7175 600  8275 600 
Text Notes 600  600  0    60   Italic 12
5V0 Regulator for uControl
$Comp
L R_1k00 R10
U 1 1 50E2BB63
P 7625 3950
F 0 "R10" H 7700 4100 50  0000 C CNN
F 1 "1k" V 7630 3950 50  0000 C CNN
F 2 "mmM:r_0805" V 7730 3950 50  0001 C CNN
F 3 "" H 7625 3950 60  0001 C CNN
F 4 "RMCF0805JT1K00" H 7625 3950 60  0001 C CNN "manf#"
	1    7625 3950
	1    0    0    -1  
$EndComp
$Comp
L R_1k00 R13
U 1 1 50E2BB2F
P 7925 1175
F 0 "R13" H 7850 1325 50  0000 C CNN
F 1 "1k" V 7930 1175 50  0000 C CNN
F 2 "mmM:r_0805" V 8030 1175 50  0001 C CNN
F 3 "" H 7925 1175 60  0001 C CNN
F 4 "RMCF0805JT1K00" H 7925 1175 60  0001 C CNN "manf#"
	1    7925 1175
	1    0    0    -1  
$EndComp
$Comp
L R_120 R9
U 1 1 50E2BB15
P 7625 1175
F 0 "R9" H 7575 1325 50  0000 C CNN
F 1 "120E" V 7630 1175 50  0000 C CNN
F 2 "mmM:r_0805" V 7730 1175 50  0001 C CNN
F 3 "" H 7625 1175 60  0001 C CNN
F 4 "RMCF0805JT120R" H 7625 1175 60  0001 C CNN "manf#"
	1    7625 1175
	1    0    0    -1  
$EndComp
$Comp
L R_330 R8
U 1 1 50E2BAF0
P 7325 1175
F 0 "R8" H 7275 1350 50  0000 C CNN
F 1 "330E" V 7330 1175 50  0000 C CNN
F 2 "mmM:r_0805" V 7430 1175 50  0001 C CNN
F 3 "" H 7325 1175 60  0001 C CNN
F 4 "RMCF0805JT330R" H 7325 1175 60  0001 C CNN "manf#"
	1    7325 1175
	1    0    0    -1  
$EndComp
$Comp
L V_IN P24
U 1 1 50E2B59E
P 1425 1750
F 0 "P24" H 1125 1950 40  0000 C CNN
F 1 "PWR_IN" H 1375 1950 40  0000 C CNN
F 2 "mmM:JACK_ALIM" H 1425 1600 60  0001 C CNN
F 3 "" H 1425 1750 60  0001 C CNN
F 4 "PJ-002B" H 1425 1750 60  0001 C CNN "manf#"
	1    1425 1750
	1    0    0    -1  
$EndComp
$Comp
L LED D7
U 1 1 50E2A47A
P 7625 4450
F 0 "D7" V 7550 4400 50  0000 C CNN
F 1 "BLINK" H 7775 4500 50  0000 C CNN
F 2 "mmM:led_0805" H 7775 4600 50  0001 C CNN
F 3 "" H 7625 4450 60  0001 C CNN
F 4 "LG M67K-H1J2-24-Z" V 7625 4450 60  0001 C CNN "manf#"
	1    7625 4450
	0    1    1    0   
$EndComp
$Comp
L LED D8
U 1 1 50E2A45A
P 7925 1675
F 0 "D8" V 7850 1625 50  0000 C CNN
F 1 "12V" H 8075 1725 50  0000 C CNN
F 2 "mmM:led_0805" H 8075 1825 50  0001 C CNN
F 3 "" H 7925 1675 60  0001 C CNN
F 4 "LG M67K-H1J2-24-Z" V 7925 1675 60  0001 C CNN "manf#"
	1    7925 1675
	0    1    1    0   
$EndComp
$Comp
L LED D6
U 1 1 50E2A449
P 7625 1675
F 0 "D6" V 7550 1625 50  0000 C CNN
F 1 "3V3" H 7775 1725 50  0000 C CNN
F 2 "mmM:led_0805" H 7775 1825 50  0001 C CNN
F 3 "" H 7625 1675 60  0001 C CNN
F 4 "LG M67K-H1J2-24-Z" V 7625 1675 60  0001 C CNN "manf#"
	1    7625 1675
	0    1    1    0   
$EndComp
$Comp
L LED D5
U 1 1 50E2A42C
P 7325 1675
F 0 "D5" V 7250 1625 50  0000 C CNN
F 1 "5V0" H 7475 1725 50  0000 C CNN
F 2 "mmM:led_0805" H 7475 1825 50  0001 C CNN
F 3 "" H 7325 1675 60  0001 C CNN
F 4 "LG M67K-H1J2-24-Z" V 7325 1675 60  0001 C CNN "manf#"
	1    7325 1675
	0    1    1    0   
$EndComp
$Comp
L D_1N4001 D4
U 1 1 50E2A12F
P 2375 1650
F 0 "D4" H 2375 1750 40  0000 C CNN
F 1 "ES1D-13-F" H 2375 1550 40  0000 C CNN
F 2 "mmM:Diode-SMA" H 2375 1650 40  0001 C CNN
F 3 "" H 2375 1650 60  0001 C CNN
F 4 "ES1D-13-F" H 2375 1650 60  0001 C CNN "manf#"
	1    2375 1650
	1    0    0    -1  
$EndComp
Text Label 7925 875  0    40   ~ 0
12V
Text HLabel 5550 3950 2    40   BiDi ~ 0
3V3
$Comp
L +3.3V #PWR012
U 1 1 50DD3EAC
P 5400 3875
F 0 "#PWR012" H 5400 3835 30  0001 C CNN
F 1 "+3.3V" H 5400 3985 30  0000 C CNN
F 2 "" H 5400 3875 60  0001 C CNN
F 3 "" H 5400 3875 60  0001 C CNN
	1    5400 3875
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR013
U 1 1 4FE44ABC
P 7625 1975
F 0 "#PWR013" H 7625 1975 30  0001 C CNN
F 1 "GND" H 7625 1905 30  0001 C CNN
F 2 "" H 7625 1975 60  0001 C CNN
F 3 "" H 7625 1975 60  0001 C CNN
	1    7625 1975
	1    0    0    -1  
$EndComp
Text Label 7625 875  0    40   ~ 0
3V3
Text Label 7325 875  0    40   ~ 0
5V0
Text Notes 7175 600  0    60   Italic 12
INDICATORS
Text Notes 7175 3075 0    60   Italic 12
BLINK LED - D13
Text Label 7400 4700 0    40   ~ 0
GND
Text HLabel 7400 3575 0    40   Input ~ 0
SCK
$Comp
L GND #PWR014
U 1 1 4FC621D3
P 7400 4750
F 0 "#PWR014" H 7400 4750 30  0001 C CNN
F 1 "GND" H 7400 4680 30  0001 C CNN
F 2 "" H 7400 4750 60  0001 C CNN
F 3 "" H 7400 4750 60  0001 C CNN
	1    7400 4750
	-1   0    0    -1  
$EndComp
Text Label 7400 3575 0    40   ~ 0
SCK
$Comp
L GND #PWR015
U 1 1 4FC61A09
P 3750 2600
F 0 "#PWR015" H 3750 2600 30  0001 C CNN
F 1 "GND" H 3750 2530 30  0001 C CNN
F 2 "" H 3750 2600 60  0001 C CNN
F 3 "" H 3750 2600 60  0001 C CNN
	1    3750 2600
	-1   0    0    -1  
$EndComp
$Comp
L PCB G4
U 1 1 4FC075DD
P 10750 5850
F 0 "G4" H 10750 5550 60  0000 C CNN
F 1 "Logo_OH" H 10750 6150 60  0000 C CNN
F 2 "mmM:OSHW_6mm" H 10750 5850 60  0001 C CNN
F 3 "" H 10750 5850 60  0001 C CNN
	1    10750 5850
	1    0    0    -1  
$EndComp
$Comp
L PCB G3
U 1 1 4FC075CE
P 10750 5150
F 0 "G3" H 10750 4850 60  0000 C CNN
F 1 "Logo_OH" H 10750 5450 60  0000 C CNN
F 2 "mmM:OSHW_6mm" H 10750 5150 60  0001 C CNN
F 3 "" H 10750 5150 60  0001 C CNN
	1    10750 5150
	1    0    0    -1  
$EndComp
$Comp
L PCB G2
U 1 1 4FC075C2
P 10750 4450
F 0 "G2" H 10750 4150 60  0000 C CNN
F 1 "Logo_Wyolum" H 10750 4750 60  0000 C CNN
F 2 "mmM:Logo-WL3" H 10750 4450 60  0001 C CNN
F 3 "" H 10750 4450 60  0001 C CNN
	1    10750 4450
	1    0    0    -1  
$EndComp
$Comp
L PCB G1
U 1 1 4FC075A6
P 10750 3750
F 0 "G1" H 10750 3450 60  0000 C CNN
F 1 "Logo_Wyolum" H 10750 4050 60  0000 C CNN
F 2 "mmM:Logo-WL3" H 10750 3750 60  0001 C CNN
F 3 "" H 10750 3750 60  0001 C CNN
	1    10750 3750
	1    0    0    -1  
$EndComp
$Comp
L CONN_2 P13
U 1 1 521B769C
P 1175 2375
F 0 "P13" V 1125 2375 40  0000 C CNN
F 1 "PWR_IN" V 1225 2375 40  0000 C CNN
F 2 "mmM:Header_2" H 1175 2375 60  0001 C CNN
F 3 "" H 1175 2375 60  0000 C CNN
F 4 "PRPC002SFAN-RC" V 1175 2375 60  0001 C CNN "manf#"
	1    1175 2375
	-1   0    0    -1  
$EndComp
Wire Notes Line
	600  3075 6725 3075
Wire Notes Line
	600  3075 600  5325
Wire Notes Line
	6725 3075 6725 5325
Text Notes 600  3075 0    60   Italic 12
3V3 Regulator for uControl
$Comp
L LM2675-5.0 U2
U 1 1 56642335
P 3600 1650
F 0 "U2" H 3300 1950 40  0000 C CNN
F 1 "LM2675-5.0" H 3450 2000 40  0000 C CNN
F 2 "mmM:SO8E" H 3600 1650 40  0001 C CIN
F 3 "" H 3600 1650 60  0000 C CNN
F 4 "LM2675MX-5.0/NOPB" H 3600 1650 60  0001 C CNN "manf#"
	1    3600 1650
	1    0    0    -1  
$EndComp
$Comp
L CP C16
U 1 1 56642343
P 5050 2050
F 0 "C16" H 5075 2150 50  0000 L CNN
F 1 "100uF 10V" V 4900 1725 50  0000 L CNN
F 2 "mmM:C_2917_HandSoldering" H 5088 1900 30  0001 C CNN
F 3 "" H 5050 2050 60  0000 C CNN
F 4 "TPSD107M010R0050" H 5050 2050 60  0001 C CNN "manf#"
	1    5050 2050
	1    0    0    -1  
$EndComp
$Comp
L C C12
U 1 1 56642351
P 4375 1500
F 0 "C12" V 4325 1575 50  0000 L CNN
F 1 "10nF" V 4225 1475 50  0000 L CNN
F 2 "mmM:c_0805" H 4413 1350 30  0001 C CNN
F 3 "" H 4375 1500 60  0000 C CNN
F 4 "CL21B103KBANNNC" V 4375 1500 60  0001 C CNN "manf#"
	1    4375 1500
	0    1    1    0   
$EndComp
$Comp
L D_Schottky D2
U 1 1 56642358
P 4550 2050
F 0 "D2" V 4425 2125 50  0000 C CNN
F 1 "SS35" H 4750 2100 50  0000 C CNN
F 2 "mmM:DO-214AB" H 4550 2050 60  0001 C CNN
F 3 "" H 4550 2050 60  0000 C CNN
F 4 "SS35" V 4550 2050 60  0001 C CNN "manf#"
	1    4550 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	4050 1650 4650 1650
Wire Wire Line
	4050 1500 4250 1500
Wire Wire Line
	4500 1500 4550 1500
Wire Wire Line
	4550 1500 4550 1900
Connection ~ 4550 1650
Wire Wire Line
	5050 1100 5050 1900
Wire Wire Line
	4850 1650 5550 1650
Wire Wire Line
	2650 900  2650 1900
Wire Wire Line
	2575 1650 3150 1650
Wire Wire Line
	2650 2475 2650 2200
Wire Wire Line
	1525 2475 5550 2475
Wire Wire Line
	5050 2475 5050 2200
Wire Wire Line
	4550 2200 4550 2475
Connection ~ 4550 2475
Wire Wire Line
	3750 2000 3750 2600
Connection ~ 3750 2475
Wire Wire Line
	5050 1100 3750 1100
Wire Wire Line
	3750 1100 3750 1300
Connection ~ 5050 1650
Connection ~ 2650 1650
Wire Wire Line
	1725 1750 1850 1750
Wire Wire Line
	1850 1750 1850 2475
Connection ~ 2650 2475
Text Label 2875 2475 0    40   ~ 0
GND
Text Label 4075 1650 0    40   ~ 0
VSW5
Text Label 4075 1500 0    40   ~ 0
CB5
Text Notes 3775 1225 0    40   ~ 0
Keep feedback wiring\naway from inductor flux
$Comp
L TEST W1
U 1 1 56642389
P 3450 2250
F 0 "W1" V 3500 2325 40  0000 C CNN
F 1 "EN" V 3425 2325 40  0000 C CNN
F 2 "mmM:r_0805" H 3450 2250 60  0001 C CNN
F 3 "" H 3450 2250 60  0000 C CNN
	1    3450 2250
	0    1    1    0   
$EndComp
Wire Wire Line
	3450 2050 3450 2000
Wire Wire Line
	3450 2450 3450 2475
Connection ~ 3450 2475
Wire Wire Line
	3600 2000 3600 2125
Wire Wire Line
	3600 2125 3900 2125
Connection ~ 3750 2125
Wire Wire Line
	3900 2125 3900 2000
Wire Wire Line
	1725 1850 1850 1850
Connection ~ 1850 1850
Text Label 1850 1650 0    40   ~ 0
PWR_IN
Wire Wire Line
	1725 1650 2175 1650
Text Notes 850  1800 0    30   Italic 6
BARREL\nPOWER\nSOCKET
Text Label 2875 1650 0    40   ~ 0
12V
Connection ~ 1850 2475
Wire Wire Line
	1525 2275 2100 2275
Wire Wire Line
	2100 2275 2100 1650
Connection ~ 2100 1650
$Comp
L PWR_FLAG #FLG016
U 1 1 56649F69
P 5225 2375
F 0 "#FLG016" H 5225 2645 30  0001 C CNN
F 1 "PWR_FLAG" H 5225 2605 30  0000 C CNN
F 2 "" H 5225 2375 60  0000 C CNN
F 3 "" H 5225 2375 60  0000 C CNN
	1    5225 2375
	1    0    0    -1  
$EndComp
Text HLabel 5800 900  2    40   BiDi ~ 0
12V
Text HLabel 5550 2475 2    40   BiDi ~ 0
GND
Text HLabel 5550 1650 2    40   BiDi ~ 0
5V0
Wire Wire Line
	5800 900  2650 900 
Connection ~ 5050 2475
Wire Wire Line
	5225 2375 5225 2475
Connection ~ 5225 2475
Text Label 5225 1650 0    40   ~ 0
5V0
Wire Wire Line
	6125 2075 5400 2075
Wire Wire Line
	5400 2075 5400 2475
Connection ~ 5400 2475
Wire Wire Line
	6125 1975 5400 1975
Wire Wire Line
	5400 1975 5400 1650
Connection ~ 5400 1650
$Comp
L GND #PWR017
U 1 1 5664E6C9
P 3750 4900
F 0 "#PWR017" H 3750 4900 30  0001 C CNN
F 1 "GND" H 3750 4830 30  0001 C CNN
F 2 "" H 3750 4900 60  0001 C CNN
F 3 "" H 3750 4900 60  0001 C CNN
	1    3750 4900
	-1   0    0    -1  
$EndComp
$Comp
L LM2675-5.0 U3
U 1 1 5664E6D5
P 3600 3950
F 0 "U3" H 3300 4250 40  0000 C CNN
F 1 "LM2675-3.3" H 3450 4300 40  0000 C CNN
F 2 "mmM:SO8E" H 3600 3950 40  0001 C CIN
F 3 "" H 3600 3950 60  0000 C CNN
F 4 "LM2675MX-3.3/NOPB" H 3600 3950 60  0001 C CNN "manf#"
	1    3600 3950
	1    0    0    -1  
$EndComp
$Comp
L CP C6
U 1 1 5664E6DB
P 2650 4350
F 0 "C6" H 2675 4450 50  0000 L CNN
F 1 "330uF 25V" H 2675 4250 50  0000 L CNN
F 2 "mmM:C_ELCO_SMD_8x10" H 2688 4200 30  0001 C CNN
F 3 "" H 2650 4350 60  0000 C CNN
F 4 "UCL1E331MNL1GS" H 2650 4350 60  0001 C CNN "manf#"
	1    2650 4350
	1    0    0    -1  
$EndComp
$Comp
L L_Small L2
U 1 1 5664E6E7
P 4750 3950
F 0 "L2" V 4825 3950 50  0000 L CNN
F 1 "33uH" V 4700 3850 50  0000 L CNN
F 2 "mmM:Choke_SMD_Wuerth-784775133" H 4750 3950 60  0001 C CNN
F 3 "" H 4750 3950 60  0000 C CNN
F 4 "784775133" V 4750 3950 60  0001 C CNN "manf#"
	1    4750 3950
	0    -1   -1   0   
$EndComp
$Comp
L C C15
U 1 1 5664E6ED
P 4375 3800
F 0 "C15" V 4325 3875 50  0000 L CNN
F 1 "10nF" V 4225 3775 50  0000 L CNN
F 2 "mmM:c_0805" H 4413 3650 30  0001 C CNN
F 3 "" H 4375 3800 60  0000 C CNN
F 4 "CL21B103KBANNNC" V 4375 3800 60  0001 C CNN "manf#"
	1    4375 3800
	0    1    1    0   
$EndComp
$Comp
L D_Schottky D10
U 1 1 5664E6F3
P 4550 4350
F 0 "D10" V 4425 4425 50  0000 C CNN
F 1 "SS35" H 4750 4400 50  0000 C CNN
F 2 "mmM:DO-214AB" H 4550 4350 60  0001 C CNN
F 3 "" H 4550 4350 60  0000 C CNN
F 4 "SS35" V 4550 4350 60  0001 C CNN "manf#"
	1    4550 4350
	0    1    1    0   
$EndComp
Wire Wire Line
	4050 3950 4650 3950
Wire Wire Line
	4050 3800 4250 3800
Wire Wire Line
	4500 3800 4550 3800
Wire Wire Line
	4550 3800 4550 4200
Connection ~ 4550 3950
Wire Wire Line
	5050 3400 5050 4200
Wire Wire Line
	4850 3950 5550 3950
Wire Wire Line
	2375 3950 3150 3950
Wire Wire Line
	2650 4775 5550 4775
Wire Wire Line
	5050 4775 5050 4500
Wire Wire Line
	4550 4500 4550 4775
Connection ~ 4550 4775
Wire Wire Line
	3750 4300 3750 4900
Connection ~ 3750 4775
Wire Wire Line
	5050 3400 3750 3400
Wire Wire Line
	3750 3400 3750 3600
Connection ~ 5050 3950
Text Label 4075 3950 0    40   ~ 0
VSW3
Text Label 4075 3800 0    40   ~ 0
CB3
Text Notes 3775 3525 0    40   ~ 0
Keep feedback wiring\naway from inductor flux
$Comp
L TEST W2
U 1 1 5664E722
P 3450 4550
F 0 "W2" V 3500 4625 40  0000 C CNN
F 1 "EN" V 3425 4625 40  0000 C CNN
F 2 "mmM:r_0805" H 3450 4550 60  0001 C CNN
F 3 "" H 3450 4550 60  0000 C CNN
	1    3450 4550
	0    1    1    0   
$EndComp
Wire Wire Line
	3450 4350 3450 4300
Wire Wire Line
	3450 4750 3450 4775
Connection ~ 3450 4775
Wire Wire Line
	3600 4300 3600 4425
Wire Wire Line
	3600 4425 3900 4425
Connection ~ 3750 4425
Wire Wire Line
	3900 4425 3900 4300
Text Label 2875 3950 0    40   ~ 0
12V
Text HLabel 5550 4775 2    40   BiDi ~ 0
GND
Connection ~ 5050 4775
Wire Wire Line
	6125 4375 5400 4375
Wire Wire Line
	5400 4375 5400 4775
Connection ~ 5400 4775
Wire Wire Line
	5400 4275 6125 4275
Wire Wire Line
	5400 3875 5400 4275
Connection ~ 5400 3950
Text Label 5200 3950 0    40   ~ 0
3V3
Wire Notes Line
	6725 5325 600  5325
Wire Wire Line
	2650 4200 2650 3950
Wire Wire Line
	2650 4500 2650 4775
Text Label 2875 4775 0    40   ~ 0
GND
$Comp
L CP C18
U 1 1 56652159
P 5050 4350
F 0 "C18" H 5075 4450 50  0000 L CNN
F 1 "100uF 10V" V 4900 4025 50  0000 L CNN
F 2 "mmM:C_2917_HandSoldering" H 5088 4200 30  0001 C CNN
F 3 "" H 5050 4350 60  0000 C CNN
F 4 "TPSD107M010R0050" H 5050 4350 60  0001 C CNN "manf#"
	1    5050 4350
	1    0    0    -1  
$EndComp
$Comp
L L_Small L1
U 1 1 566522D7
P 4750 1650
F 0 "L1" V 4825 1650 50  0000 L CNN
F 1 "33uH" V 4700 1550 50  0000 L CNN
F 2 "mmM:Choke_SMD_Wuerth-784775133" H 4750 1650 60  0001 C CNN
F 3 "" H 4750 1650 60  0000 C CNN
F 4 "784775133" V 4750 1650 60  0001 C CNN "manf#"
	1    4750 1650
	0    -1   -1   0   
$EndComp
$Comp
L CP C5
U 1 1 56652F17
P 2650 2050
F 0 "C5" H 2675 2150 50  0000 L CNN
F 1 "330uF 25V" H 2200 1925 50  0000 L CNN
F 2 "mmM:C_ELCO_SMD_8x10" H 2688 1900 30  0001 C CNN
F 3 "" H 2650 2050 60  0000 C CNN
F 4 "UCL1E331MNL1GS" H 2650 2050 60  0001 C CNN "manf#"
	1    2650 2050
	1    0    0    -1  
$EndComp
$Comp
L PWR_FLAG #FLG018
U 1 1 56654415
P 2800 1500
F 0 "#FLG018" H 2800 1770 30  0001 C CNN
F 1 "PWR_FLAG" H 2800 1730 30  0000 C CNN
F 2 "" H 2800 1500 60  0000 C CNN
F 3 "" H 2800 1500 60  0000 C CNN
	1    2800 1500
	1    0    0    -1  
$EndComp
Wire Wire Line
	2800 1500 2800 2725
Connection ~ 2800 1650
$Comp
L CONN_3 J2
U 1 1 5665ADBC
P 6475 4375
F 0 "J2" V 6425 4375 50  0000 C CNN
F 1 "3V3_EXT" V 6525 4375 50  0000 C CNN
F 2 "mmM:Header_3" H 6475 4375 60  0001 C CNN
F 3 "" H 6475 4375 60  0000 C CNN
F 4 "PREC003SAAN-RC" V 6475 4375 60  0001 C CNN "manf#"
	1    6475 4375
	1    0    0    -1  
$EndComp
Wire Wire Line
	2375 3950 2375 5100
Wire Wire Line
	2375 5100 5925 5100
Wire Wire Line
	5925 5100 5925 4475
Wire Wire Line
	5925 4475 6125 4475
Connection ~ 2650 3950
$Comp
L CONN_3 J1
U 1 1 5665B6DA
P 6475 2075
F 0 "J1" V 6425 2075 50  0000 C CNN
F 1 "5V_EXT" V 6525 2075 50  0000 C CNN
F 2 "mmM:Header_3" H 6475 2075 60  0001 C CNN
F 3 "" H 6475 2075 60  0000 C CNN
F 4 "PREC003SAAN-RC" V 6475 2075 60  0001 C CNN "manf#"
	1    6475 2075
	1    0    0    -1  
$EndComp
Wire Wire Line
	2800 2725 5925 2725
Wire Wire Line
	5925 2725 5925 2175
Wire Wire Line
	5925 2175 6125 2175
$EndSCHEMATC