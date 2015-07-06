EESchema Schematic File Version 2
LIBS:Conn-raspberry
LIBS:power
LIBS:uControl
LIBS:uControl_v3-cache
EELAYER 27 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 4 5
Title "uControl"
Date "1 jan 2014"
Rev "1"
Comp "WyoLum"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L DS3231N U5
U 1 1 50E2C1B1
P 5550 2800
F 0 "U5" H 5850 3350 60  0000 C CNN
F 1 "DS3231N" H 5250 2400 60  0000 C CNN
F 2 "DS3231" H 5250 2500 60  0001 C CNN
F 3 "" H 5550 2800 60  0001 C CNN
F 4 "IC RTC W/TCXO 16-SOIC" H 5550 3450 60  0001 L CNN "Field4"
F 5 "Clock/Calendar" H 5550 3550 60  0001 L CNN "Field5"
F 6 "16-SOIC (0.295\", 7.50mm Width)" H 5550 3650 60  0001 L CNN "Field6"
F 7 "Maxim Integrated" H 5550 3750 60  0001 L CNN "Field7"
F 8 "DS3231S#" H 5550 3850 60  0001 L CNN "Field8"
F 9 "Digikey" H 5550 3950 60  0001 L CNN "Field9"
F 10 "DS3231S#-ND" H 5550 4050 60  0001 L CNN "Field10"
F 11 "http://www.digikey.com/product-detail/en/DS3231S%23/DS3231S%23-ND/1197574" H 5550 4150 60  0001 L CNN "Field11"
	1    5550 2800
	1    0    0    -1  
$EndComp
$Comp
L R_10K R11
U 1 1 50E2B876
P 7150 2000
F 0 "R11" H 7050 2150 50  0000 C CNN
F 1 "10k" V 7155 2000 50  0000 C CNN
F 2 "r_0805" V 7255 2000 50  0001 C CNN
F 3 "" H 7150 2000 60  0001 C CNN
F 4 "RES 10K OHM 1/8W 5% CF AXIAL" H 7150 2100 60  0001 L CNN "Field4"
F 5 "0.125W, 1/8W" H 7150 2200 60  0001 L CNN "Field5"
F 6 "Axial" H 7150 2300 60  0001 L CNN "Field6"
F 7 "Stackpole Electronics Inc" H 7150 2400 60  0001 L CNN "Field7"
F 8 "CF18JT10K0" H 7150 2500 60  0001 L CNN "Field8"
F 9 "Digikey" H 7150 2600 60  0001 L CNN "Field9"
F 10 "CF18JT10K0CT-ND" H 7150 2700 60  0001 L CNN "Field10"
F 11 "http://www.digikey.com/product-detail/en/CF18JT10K0/CF18JT10K0CT-ND/2022766?cur=USD" H 7150 2800 60  0001 L CNN "Field11"
	1    7150 2000
	1    0    0    -1  
$EndComp
$Comp
L C C23
U 1 1 50E2955A
P 4175 2775
F 0 "C23" H 4175 2875 50  0000 L CNN
F 1 "100nF" V 4250 2450 50  0000 L CNN
F 2 "c_0805" H 4175 2775 50  0001 C CNN
F 3 "" H 4175 2775 60  0001 C CNN
F 4 "CAP FILM 0.1UF 63VDC RADIAL" H 4175 2975 60  0001 L CNN "Field4"
F 5 "100nF, 63V" H 4175 3075 60  0001 L CNN "Field5"
F 6 "R82" H 4175 3175 60  0001 L CNN "Field6"
F 7 "Kemet" H 4175 3275 60  0001 L CNN "Field7"
F 8 "R82DC3100AA50J" H 4175 3375 60  0001 L CNN "Field8"
F 9 "Digikey" H 4175 3475 60  0001 L CNN "Field9"
F 10 "399-5863-ND" H 4175 3575 60  0001 L CNN "Field10"
F 11 "http://www.digikey.com/product-detail/en/R82DC3100AA50J/399-5863-ND/2571298?cur=USD" H 4175 3675 60  0001 L CNN "Field11"
	1    4175 2775
	1    0    0    -1  
$EndComp
$Comp
L BATT_COIN BT2
U 1 1 50E29191
P 3525 2825
F 0 "BT2" V 3400 2600 50  0000 L CNN
F 1 "BATT_COIN" H 3525 2635 50  0000 L CNN
F 2 "" H 3525 2825 60  0001 C CNN
F 3 "" H 3525 2825 60  0001 C CNN
F 4 "BATTERY LITHIUM COIN 3V 20MM" H 3525 3125 60  0001 L CNN "Field4"
F 5 "Lithium, 3V, 225mAh" H 3525 3225 60  0001 L CNN "Field5"
F 6 "CR2032" H 3525 3325 60  0001 L CNN "Field6"
F 7 "Panasonic - BSG" H 3525 3425 60  0001 L CNN "Field7"
F 8 "CR2032" H 3525 3525 60  0001 L CNN "Field8"
F 9 "Digikey" H 3525 3625 60  0001 L CNN "Field9"
F 10 "P189-ND" H 3525 3725 60  0001 L CNN "Field10"
F 11 "http://www.digikey.com/product-detail/en/CR2032/P189-ND/31939?cur=USD" H 3525 3825 60  0001 L CNN "Field11"
	1    3525 2825
	0    1    1    0   
$EndComp
$Comp
L BATT_HOLDER BT1
U 1 1 50E29166
P 3950 2800
F 0 "BT1" V 3850 2625 50  0000 L CNN
F 1 "BATT_HOLDER" H 3975 2675 50  0000 L CNN
F 2 "CR2032" H 3950 2900 60  0001 L CNN
F 3 "" H 3950 2800 60  0001 C CNN
F 4 "HOLDER BATTERY COIN 20MM DIA THM" H 3950 3100 60  0001 L CNN "Field4"
F 5 "Coin Cell, Retainer" H 3950 3200 60  0001 L CNN "Field5"
F 6 "Coin, 20.0mm" H 3950 3300 60  0001 L CNN "Field6"
F 7 "Keystone Electronics" H 3950 3400 60  0001 L CNN "Field7"
F 8 "3003" H 3950 3500 60  0001 L CNN "Field8"
F 9 "Digikey" H 3950 3600 60  0001 L CNN "Field9"
F 10 "3003K-ND" H 3950 3700 60  0001 L CNN "Field10"
F 11 "http://www.digikey.com/scripts/DkSearch/dksus.dll?x=0&y=0&lang=en&KeyWords=3003K-ND&cur=USD" H 3950 3800 60  0001 L CNN "Field11"
	1    3950 2800
	0    1    1    0   
$EndComp
Text Label 6500 2450 0    40   ~ 0
SQR
Wire Wire Line
	9050 4800 8000 4800
Wire Wire Line
	9050 4500 8000 4500
Connection ~ 7150 1675
Wire Wire Line
	7150 1750 7150 1675
Wire Wire Line
	9050 3750 8000 3750
Wire Wire Line
	8000 3750 8000 1675
Wire Wire Line
	8000 1675 4375 1675
Wire Wire Line
	6450 2600 7500 2600
Wire Wire Line
	9050 4000 4500 4000
Wire Wire Line
	4500 4000 4500 2850
Wire Wire Line
	4500 2850 4650 2850
Connection ~ 3950 3100
Wire Wire Line
	3950 3100 4175 3100
Wire Wire Line
	4175 3100 4175 2900
Wire Wire Line
	3950 1900 3950 2550
Wire Wire Line
	3950 1900 5300 1900
Connection ~ 6575 3150
Wire Wire Line
	6575 3150 6450 3150
Connection ~ 6575 2950
Wire Wire Line
	6450 2950 6575 2950
Connection ~ 5850 3750
Wire Wire Line
	5850 3750 5850 3650
Wire Wire Line
	5750 3750 5750 3650
Wire Wire Line
	6575 3750 6575 2850
Wire Wire Line
	6575 2850 6450 2850
Wire Wire Line
	4650 2600 4375 2600
Connection ~ 5750 3750
Wire Wire Line
	5950 3750 5950 3650
Connection ~ 5950 3750
Wire Wire Line
	6575 3050 6450 3050
Connection ~ 6575 3050
Wire Wire Line
	6450 3250 6575 3250
Connection ~ 6575 3250
Wire Wire Line
	4650 2450 4375 2450
Wire Wire Line
	3950 3000 3950 3750
Wire Wire Line
	3950 3750 6575 3750
Connection ~ 4375 3750
Wire Wire Line
	4175 2650 4175 2425
Wire Wire Line
	4175 2425 3950 2425
Connection ~ 3950 2425
Wire Wire Line
	4375 2450 4375 1675
Wire Wire Line
	4650 3000 4550 3000
Wire Wire Line
	4550 3000 4550 3875
Wire Wire Line
	4550 3875 9050 3875
Wire Wire Line
	6450 2450 7500 2450
Wire Wire Line
	7500 2750 6450 2750
Wire Wire Line
	4375 2600 4375 4125
Wire Wire Line
	4375 4125 9050 4125
Wire Wire Line
	5300 1850 5300 2000
Connection ~ 5300 1900
Wire Wire Line
	7150 2250 7150 2450
Connection ~ 7150 2450
Wire Wire Line
	9050 4350 8000 4350
Wire Wire Line
	9050 4650 8000 4650
Text Label 8000 4800 0    40   ~ 0
RST
Text Label 8000 4650 0    40   ~ 0
SQR
Text Label 8000 4500 0    40   ~ 0
32k
Text Label 8000 4350 0    40   ~ 0
BAT
Text HLabel 9050 4800 2    60   Input ~ 0
RST
Text HLabel 9050 4650 2    60   Input ~ 0
SQR
Text HLabel 9050 4500 2    60   Input ~ 0
32k
Text HLabel 9050 4350 2    60   Input ~ 0
BAT
$Comp
L +BATT #PWR021
U 1 1 4EC101F0
P 5300 1850
F 0 "#PWR021" H 5300 1800 20  0001 C CNN
F 1 "+BATT" H 5300 1950 30  0000 C CNN
F 2 "" H 5300 1850 60  0001 C CNN
F 3 "" H 5300 1850 60  0001 C CNN
	1    5300 1850
	1    0    0    -1  
$EndComp
Text HLabel 9050 4125 2    60   Input ~ 0
GND
Text HLabel 9050 4000 2    60   Input ~ 0
SDA
Text HLabel 9050 3875 2    60   Input ~ 0
SCL
Text HLabel 9050 3750 2    60   Input ~ 0
5V0
Text Label 8050 3750 0    40   ~ 0
5V0
Text Label 8050 4125 0    40   ~ 0
GND
$Comp
L I_O B3
U 1 1 4E1FEBD4
P 7650 2750
F 0 "B3" H 7730 2750 40  0000 L CNN
F 1 "I_O" H 7650 2805 30  0001 C CNN
F 2 "I_O" H 7650 2750 60  0001 C CNN
F 3 "" H 7650 2750 60  0001 C CNN
	1    7650 2750
	1    0    0    -1  
$EndComp
$Comp
L I_O B2
U 1 1 4E1FEBCE
P 7650 2600
F 0 "B2" H 7730 2600 40  0000 L CNN
F 1 "I_O" H 7650 2655 30  0001 C CNN
F 2 "I_O" H 7650 2600 60  0001 C CNN
F 3 "" H 7650 2600 60  0001 C CNN
	1    7650 2600
	1    0    0    -1  
$EndComp
$Comp
L I_O B1
U 1 1 4E1FEBC6
P 7650 2450
F 0 "B1" H 7730 2450 40  0000 L CNN
F 1 "I_O" H 7650 2505 30  0001 C CNN
F 2 "I_O" H 7650 2450 60  0001 C CNN
F 3 "" H 7650 2450 60  0001 C CNN
	1    7650 2450
	1    0    0    -1  
$EndComp
Text Label 4750 3750 0    40   ~ 0
GND
Text Label 3950 1900 0    40   ~ 0
BAT
Text Label 8050 3875 0    40   ~ 0
SCL
Text Label 8050 4000 0    40   ~ 0
SDA
Text Label 6500 2600 0    40   ~ 0
RST
Text Label 6500 2750 0    40   ~ 0
32k
$EndSCHEMATC
