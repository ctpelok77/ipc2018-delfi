(define (domain simple-walk)
(:predicates
     (at ?x) (connected ?x ?y))
(:action walk
 :parameters (?location1 ?location2)
 :precondition
    (and (at ?location1) (connected ?location1 ?location2))
 :effect
    (and (not (at ?location1)) (at ?location2)))
)
