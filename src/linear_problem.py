import numpy as np
from typing import Union, cast


def assign(voeux: np.ndarray, temps_trajet: np.ndarray, tau: float = 2.0) -> np.ndarray:
    """
    Fonction principale pour assigner les équipes aux compétitions en fonction de leurs voeux et des temps de trajet.
    
    Args:
        voeux (np.ndarray): Matrice des rangs de choix (1 pour le premier choix, 2 pour le deuxième, etc.)
        temps_trajet (np.ndarray): Matrice des temps de trajet entre les équipes et les événements.
        tau (float): La durée qu'il faut ajouter pour diviser la pénalité de proximité par 2.
            L'unité de temps doit être la même que celle utilisée pour le temps de trajet (par exemple, secondes ou heures).
    
    Returns:
        np.ndarray: Indice de la compétition attribuée à chaque équipe (0 pour la première compétition, 1 pour la deuxième, etc.)
    """
    couts = matrice_couts(voeux, temps_trajet, tau)
    return resolution(couts)


def insatisfaction(rang: Union[int, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Calcule l'insatisfaction d'une équipe en fonction du rang du voeu qui lui a été attribué.
    
    Args:
        rang (int ou np.ndarray): Le rang du voeu attribué à l'équipe (1 pour le premier choix, 2 pour le deuxième, etc.)
    
    Returns:
        float ou np.ndarray: L'insatisfaction calculée pour ce rang.
    """
    return 2**(rang - 1)


def proximite(temps_trajet: Union[float, np.ndarray], tau: float = 2.0) -> Union[float, np.ndarray]:
    """
    Calcule la pénalité de proximité en fonction de la distance entre l'équipe et le lieu de l'événement.
    
    Args:
        temps_trajet (float ou np.ndarray): La durée du trajet entre l'équipe et le lieu de l'événement.
        tau (float): La durée qu'il faut ajouter pour diviser la pénalité de proximité par 2.
            L'unité de temps doit être la même que celle utilisée pour le temps de trajet (par exemple, secondes ou heures).
    
    Returns:
        float ou np.ndarray: La pénalité de proximité calculée.
    """
    return 2**(-temps_trajet / tau)


def matrice_couts(voeux: np.ndarray, temps_trajet: np.ndarray, tau: float = 2.0) -> np.ndarray:
    """
    Calcule la matrice des coûts en combinant l'insatisfaction liée au rang du voeu et la pénalité de proximité.
    
    Args:
        voeux (np.ndarray): Matrice des rangs de choix (1 pour le premier choix, 2 pour le deuxième, etc.)
        temps_trajet (np.ndarray): Matrice des temps de trajet entre les équipes et les événements.
        tau (float): La durée qu'il faut ajouter pour diviser la pénalité de proximité par 2.
            L'unité de temps doit être la même que celle utilisée pour le temps de trajet (par exemple, secondes ou heures).
    
    Returns:
        np.ndarray: Matrice des coûts calculée.
    """
    assert voeux.shape == temps_trajet.shape, "Les matrices des voeux et des temps de trajet doivent avoir la même forme."
    
    matrice_insatisfaction = insatisfaction(voeux)
    matrice_proximite = proximite(temps_trajet, tau)
    # cast est juste là pour que l'IDE me laisse tranquille
    return cast(np.ndarray, matrice_insatisfaction - matrice_proximite)


def resolution(matrice_couts: np.ndarray) -> np.ndarray:
    """
    Résout le problème d'affectation.
    
    Args:
        matrice_couts (np.ndarray): Matrice des coûts à minimiser.
    
    Returns:
        np.ndarray: Indice de la compétition attribuée à chaque équipe (0 pour la première compétition, 1 pour la deuxième, etc.)
    """
    import cvxpy as cp
    
    num_equipes, num_compets = matrice_couts.shape

    # Variables de décision
    Z = cp.Variable((num_equipes, num_compets), boolean=True)
    # Fonction objectif
    objective = cp.Minimize(cp.trace(matrice_couts.T @ Z))
    # Contraintes
    constraints = [
        Z @ np.ones(num_compets) == np.ones(num_equipes),    # Chaque équipe est assignée à un unique événement
        Z.T @ np.ones(num_equipes) >= 8*np.ones(num_compets), # Capacités minimales
        Z.T @ np.ones(num_equipes) <= 24*np.ones(num_compets)  # Capacités maximales
    ]
    problem = cp.Problem(objective, constraints)
    problem.solve()
    
    return np.argmax(Z.value, axis=1)  # Retourne l'indice de la compétition attribuée à chaque équipe
