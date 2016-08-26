(define (domain simple-drive)
(:requirements :adl)
(:predicates
     (at ?x ?y) (location ?x) (truck ?x))

(:action drive-all-l2
 :parameters (?truck)
; comment the following precondition in to remove any symmetry from the task
; :precondition
;    (and (at truck1 location0))
 :effect
  (when (truck ?truck)
        (at ?truck location2)
        ; for correct planning, we would need to set at ?truck to false for all other locations
  )
)

)
