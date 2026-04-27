;;;
; start of one solid block extrusion 
;;;

M950 P0 C"vfd"
M280 P0 S0

M208 U115 S0 ; temperary increase limit 
G1 U{initial_u_offset} ; move u to initial offset
G91 ; set all axis to relative positioning  

; extrude and z move 
G1 U{block_height} F600 ; extrude solid block 

; move to extrude point, first fast and approach slow
G1 Z-{fast_z_move_distance} F1800
G1 Z-{approach_z_move_distance} F200; 

; cut
G4 P500 ; hold
M280 P0 S60 ; cut
G4 P1000 ;wait for cut to finish

G1 Z{approach_z_move_distance} F200; move back up
G1 Z{fast_z_move_distance} F1800; move back up

M280 P0 S0 ; uncut 
G4 P1000 ; wait for uncut to finish

; reset 
G90
M208 U95 S0 ; reset extrusion liimt 
; G28 U ; re-zero U axis
; G1 F1800.000 ; reset speed

