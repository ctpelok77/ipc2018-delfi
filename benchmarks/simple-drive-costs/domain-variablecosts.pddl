(define (domain simple-drive)
(:requirements :action-costs)
(:functions
     (total-cost) - number
     (distance ?x ?y) - number)
(:predicates
     (at ?x ?y) (location ?x) (truck ?x))
(:action drive
 :parameters (?truck ?location1 ?location2)
 :precondition
    (and (truck ?truck) (location ?location1) (location ?location2) (at ?truck ?location1))
 :effect
    (and (not (at ?truck ?location1)) (at ?truck ?location2)
         (increase (total-cost) (distance ?location1 ?location2))))
)
