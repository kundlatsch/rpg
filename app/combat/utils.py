def calculate_arena_points(attacker_points, defender_points, attacker_won):
    diff = abs(attacker_points - defender_points)

    if diff < 50:
        delta = 30
    elif diff < 150:
        delta = 20
    elif diff < 300:
        delta = 10
    else:
        delta = 5

    if attacker_won:
        return delta, -delta
    else:
        return -delta, delta
