(define (problem drive-2trucks) (:domain simple-drive)
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

    (= (total-cost) 0)
)

(:goal (and
        (at truck0 location2)
        (at truck1 location2)
    )
)
(:metric minimize (total-cost))
)
