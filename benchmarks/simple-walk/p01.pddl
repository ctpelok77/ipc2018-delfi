(define (problem walk-3) (:domain simple-walk)
(:objects
    location0 location1 location2)
(:init
    (connected location0 location1)
    (connected location1 location2)
    (at location0)
)

(:goal
        (at location2)

))
