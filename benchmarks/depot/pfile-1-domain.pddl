(define (domain depot)
(:predicates
     (at ?x ?y) (in ?x ?y) (place ?x) (truck ?x) (crate ?x) )
(:action drive
 :parameters ( ?x ?y ?z)
 :precondition
    (and (truck ?x) (place ?y) (place ?z)  (at ?x ?y))
 :effect
    (and (at ?x ?z) (not (at ?x ?y))))

(:action load
 :parameters ( ?crate ?truck ?place)
 :precondition
    (and (crate ?crate) (truck ?truck) (place ?place) (at ?truck ?place) (at ?crate ?place))
 :effect
    (and (not (at ?crate ?place)) (in ?crate ?truck)))

(:action unload
 :parameters ( ?surface ?crate ?truck ?place)
 :precondition
    (and (crate ?crate) (truck ?truck) (place ?place) (at ?truck ?place) (in ?crate ?truck))
 :effect
    (and (not (in ?crate ?truck)) (at ?crate ?place)))

)
