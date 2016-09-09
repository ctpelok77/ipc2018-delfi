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
    (= (distance location0 location1) 1)
    (= (distance location1 location0) 1)
    (= (distance location0 location2) 2)
    (= (distance location2 location0) 2)
    (= (distance location1 location2) 2) ;use 3 to remove symmetries
    (= (distance location2 location1) 2) ;use 3 to remove symmetries
)

(:goal (and
        (at truck0 location2)
        (at truck1 location2)
    )
)
(:metric minimize (total-cost))
)
