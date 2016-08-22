(define (problem depotprob1818) (:domain Depot)
(:objects
    place0 place1 place2 truck0 crate0 )
(:init
    (place place0)
    (place place1)
    (place place2)

    (truck truck0)
    (at truck0 place0)

    (crate crate0)
    (at crate0 place1)
)

(:goal (and
        (at crate0 place2)
    )
))
