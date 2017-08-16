(define (problem drive-2trucks) (:domain simple-drive-axioms)
(:objects
    location0 location1 location2 truck0 truck1)
(:init
    (location location0)
    (location location1)
    (location location2)
    (truck truck0)
    (truck truck1)

    (at truck0 location0)
    (at truck1 location1)
)

(:goal (and
        (goal truck0)
        (goal truck1)
    )
))
