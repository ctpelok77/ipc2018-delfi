(define (problem twotrucks-twocrates-symmetry) (:domain simple-logistics)
(:objects
    place0 place1 place2 truck0 truck1 crate0 crate1 )
(:init
    (place place0)
    (place place1)
    (place place2)

    (truck truck0)
    (at truck0 place0)
    (truck truck1)
    (at truck1 place1)

    (crate crate0)
    (at crate0 place1)
    (crate crate1)
    (at crate1 place0)
)

(:goal (and
        (at crate0 place2)
        (at crate1 place2)
    )
))
