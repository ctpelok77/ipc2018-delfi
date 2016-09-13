(define (domain simple-drive-axioms)
(:predicates
    (at ?x ?y) (location ?x) (truck ?x) (goal ?x))
(:action drive
 :parameters (?truck ?location1 ?location2)
 :precondition
    (and (truck ?truck) (location ?location1) (location ?location2) (at ?truck ?location1))
 :effect
    (and (not (at ?truck ?location1)) (at ?truck ?location2)))
(:derived (goal ?truck)
    (and (at ?truck location2)))
)
