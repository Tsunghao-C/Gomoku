# Gomoku
42 AI project | building Gomoku AI game


## Key concetps
1. MiniMax algorithm: two players, one looking for max, the other looing for min
2. Alpha-Beta pruning: ignore branches that aleady known is poor in performance
3. Deep limiting: limiting layer of recursive function to balance process time (with an activation function or score since it may not reach to termination yet)

4. Evaluation function: a way to calculate the current state to identify which side is having advantage
    Eval function can be tricky, but we can use ML/DL to train a model that predit the state better.


## Strategies to consider
1. Priorities the neiboring locations close to existing coordinates. These could be more relevant. (I.E, Give weights to empty places based on how close are they to already occupied places)
2. 