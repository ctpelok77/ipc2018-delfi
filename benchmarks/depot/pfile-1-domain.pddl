(define (domain depot)
(:predicates
     (at ?x ?y) (in ?x ?y) (place ?x) (truck ?x) (crate ?x) )
(:action drive
 :parameters (?truck ?place1 ?place2)
 :precondition
    (and (truck ?truck) (place ?place1) (place ?place2)  (at ?truck ?place1))
 :effect
    (and (not (at ?truck ?place1)) (at ?truck ?place2)))

(:action load
 :parameters (?crate ?truck ?place)
 :precondition
    (and (crate ?crate) (truck ?truck) (place ?place) (at ?truck ?place) (at ?crate ?place))
 :effect
    (and (not (at ?crate ?place)) (in ?crate ?truck)))

(:action unload
 :parameters (?crate ?truck ?place)
 :precondition
    (and (crate ?crate) (truck ?truck) (place ?place) (at ?truck ?place) (in ?crate ?truck))
 :effect
    (and (not (in ?crate ?truck)) (at ?crate ?place)))

)
