(define (domain simple-drive)
(:predicates
     (at ?x ?y) (location ?x) (truck ?x))
(:action drive-0-2
 :parameters (?truck)
 :precondition
    (and (truck ?truck) (at ?truck location0))
 :effect
    (and (not (at ?truck location0)) (at ?truck location2)))
)
