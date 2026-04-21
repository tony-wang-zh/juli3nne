
;;;;;;;;;;;
; STARTING PART 1.STL 
;;;;;;;;;;;
G28 U0 F1000;
G01 X5.9 Y40 Z143.5 F1500; insert comment
G01 Y15 Z143.5 F500; picking tool 1 
G01 Y15 Z160 F500; insert comment
G01 Y50 Z160 F500; insert comment
G01 Y110 F1000; move away for more space
G1 X189.993 Y208.002 ; move to dispense point
G1 Z2.0 ; move to dispense point
; one powder dispense 
G1 U25 ; initial 25.0 
G1 U38 ; max 36.0
G1 U25 ; reset 
; powder dispense finished
G1 X179.988 Y208.0 ; move to dispense point
G1 Z2.0 ; move to dispense point
; one powder dispense 
G1 U25 ; initial 25.0 
G1 U38 ; max 36.0
G1 U25 ; reset 
; powder dispense finished
G28 U0 F1000;
G01 Z160;
G01 X5.9 Y40 F1500; get in front of proper tool post
G01 Y13 Z159 F500; dropping tool 1 
G01 Y11 Z157.5 F500; insert comment
G01 Y9 Z143.5 F500; insert comment
G01 Y110 F1000; move away for more space
G01 Z60.4 F5000
G01 X0.0 Y200.00 Z80.00 F2000.00
;;;;;;;;;;;
; UNDING PART 1.STL 
;;;;;;;;;;;
