import math




def hill_score(distance_m, a=517, n=2.75):
    """
    0-100 accuracy score. Exact max (100) at distance=0, unlike a
    logistic sigmoid. a = distance at which score = 50. n = steepness
    of the S-shaped transition (higher = sharper drop around a).
    """
    if distance_m is None:
        return None
    if distance_m == 0:
        return 100.0
    return 100 / (1 + (distance_m / a) ** n)


#Inspiration for formula was the fermi-dirac distribution, but the hill function is more flexible and has a sharper dropoff at the transition point.
# Formula is left as a comment for reference, but not used in the code.
    """ def fermi_score(distance_m, d0=517, T=100):
    """
    Fermi-Dirac inspired accuracy score, 0-1.
    d0: distance at which score = 0.5 (517m, near the 5%-by-chance radius)
    T: transition width — smaller = sharper cutoff, larger = more gradual
    """
    if distance_m is None:
        return None
    return 1 / (1 + math.exp((distance_m - d0) / T)) """

