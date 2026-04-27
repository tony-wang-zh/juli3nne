
;;;;;;;;;;;
; STARTING PART 1.STL 
;;;;;;;;;;;
G28 U0 F1000;
G01 X2 Y90 Z140 F1500; insert comment
G01 Y38 Z140 F500; picking tool 1 
G01 Y38 Z160 F500; insert comment
G01 Y90 Z165 F500; insert comment
G01 Y110 F1000; move away for more space
G1 X189.993 Y208.002 ; move to dispense point
G1 Z59.0 ; move to dispense point
;;;
; start of one solid block extrusion 
;;;

M208 U115 S0 ; temperary increase limit 
G1 U50.000 ; move u to initial offset
G91 ; set all axis to relative positioning  

; extrude and z move 
G1 U15.000 F600 ; extrude solid block 

; move to extrude point, first fast and approach slow
G1 Z-44.000 F1800
G1 Z-10.000 F200; 

; cut
G4 P500 ; hold
M280 P0 S60 ; cut
G4 P1000 ;wait for cut to finish

G1 Z10.000 F200; move back up
G1 Z44.000 F1800; move back up

M280 P0 S0 ; uncut 
G4 P1000 ; wait for uncut to finish

; reset 
G90
M208 U95 S0 ; reset extrusion liimt 
; G28 U ; re-zero U axis
; G1 F1800.000 ; reset speed


G1 X179.988 Y208.0 ; move to dispense point
G1 Z59.0 ; move to dispense point
;;;
; start of one solid block extrusion 
;;;

M208 U115 S0 ; temperary increase limit 
G1 U65.000 ; move u to initial offset
G91 ; set all axis to relative positioning  

; extrude and z move 
G1 U15.000 F600 ; extrude solid block 

; move to extrude point, first fast and approach slow
G1 Z-44.000 F1800
G1 Z-10.000 F200; 

; cut
G4 P500 ; hold
M280 P0 S60 ; cut
G4 P1000 ;wait for cut to finish

G1 Z10.000 F200; move back up
G1 Z44.000 F1800; move back up

M280 P0 S0 ; uncut 
G4 P1000 ; wait for uncut to finish

; reset 
G90
M208 U95 S0 ; reset extrusion liimt 
; G28 U ; re-zero U axis
; G1 F1800.000 ; reset speed


G28 U0 F1000;
G01 Z165;
G01 X2 Y80 F1500; get in front of proper tool post
G01 Y39 Z161 F500; dropping tool 1 
G01 Y32.7 Z158 F500; insert comment
G01 Y32.7 Z144 F500; insert comment
G01 Y110 F1000; move away for more space
G01 Z60.4 F5000
G01 X0.0 Y200.00 Z80.00 F2000.00
;;;;;;;;;;;
; UNDING PART 1.STL 
;;;;;;;;;;;
