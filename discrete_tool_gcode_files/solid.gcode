; first move U to inital offset 
; move z up by block height 

M950 P0 C"vfd"
M280 P0 S0

M208 U110 S0 ; temperary increase limit 

;; move to 1st solid block point 
G1 X240 Y313

G1 U78.6 ;extrude to initial + height 
G1 Z10;
G1 Z7.3 F200; move to extrude point slowly 7.3 = current print plane + 7.3
G1 F1800.000

M280 P0 S60 ; cut
G4 P1000 ;wait for cut to finish
G1 Z30  ;move up

M280 P0 S0 ; uncut 
G4 P1000 



; second part 
G1 X214.1
G1 U94.5
G1 Z7.3 F200; move to extrude point slowly
G1 F1800.000

M280 P0 S60 ; cut
G4 P1000 ;wait for cut to finish
G1 Z30  ;move up 

M280 P0 S0 ; uncut 
G4 P1000 
