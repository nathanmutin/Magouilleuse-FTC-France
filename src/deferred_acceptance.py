import numpy as np
from typing import Union, cast


def assign(voeux: np.ndarray, temps_trajet: np.ndarray) -> np.ndarray:
    """
    Fonction principale pour assigner les équipes aux compétitions en fonction de leurs voeux et des temps de trajet.
    Implementation de l'algorithme de Gale-Shapley (deferred acceptance) pour résoudre le problème d'affectation.
    
    Args:
        voeux (np.ndarray): Matrice des rangs de choix (1 pour le premier choix, 2 pour le deuxième, etc.)
        temps_trajet (np.ndarray): Matrice des temps de trajet entre les équipes et les événements.
    
    Returns:
        np.ndarray: Indice de la compétition attribuée à chaque équipe (0 pour la première compétition, 1 pour la deuxième, etc.)
    """
    
    rang_choix = -np.ones(voeux.shape[0], dtype=int)  # Rang du choix actuel pour chaque équipe (-1 avant de commencer)
    assignations = -np.ones(voeux.shape[0], dtype=int)  # Compétition actuellement assignée à chaque équipe (-1 si aucune)
    
    # Tant que toutes les équipes n'ont pas été assignées
    while np.any(assignations == -1):
        # On trouve les équipes qui n'ont pas encore été assignées
        equipes_non_assignées = np.where(assignations == -1)[0]
        # Pour chaque équipe non assignée, on propose sa prochaine compétition préférée
        for equipe in equipes_non_assignées:
            rang_choix[equipe] += 1  # On passe au rang de choix suivant
            # Si l'équipe a épuisé tous ses choix, on ne peut pas trouver de solution
            if rang_choix[equipe] >= voeux.shape[1]:
                raise ValueError(f"L'équipe {equipe} a épuisé tous ses choix sans être assignée.")
            
            competition_proposée = np.where(voeux[equipe] == rang_choix[equipe] + 1)[0][0]  # Compétition proposée à l'équipe
            # On vérifie si la compétition proposée a de la place (moins de 24 équipes assignées)
            if np.sum(assignations == competition_proposée) < 24:
                assignations[equipe] = competition_proposée  # On assigne l'équipe à la compétition proposée
            else:
                # Si la compétition est pleine, on doit vérifier si l'équipe peut "déloger" une équipe déjà assignée
                equipes_assignées = np.where(assignations == competition_proposée)[0]
                # On trouve l'équipe la plus éloignée parmi les équipes assignées à cette compétition
                equipe_la_plus_eloignee = equipes_assignées[np.argmax(temps_trajet[equipes_assignées, competition_proposée])]
                # Si l'équipe actuelle est plus proche que l'équipe la plus éloignée, on la remplace
                if temps_trajet[equipe, competition_proposée] < temps_trajet[equipe_la_plus_eloignee, competition_proposée]:
                    assignations[equipe_la_plus_eloignee] = -1  # L'équipe la plus éloignée est délogée
                    assignations[equipe] = competition_proposée  # On assigne l'équipe actuelle à la compétition proposée
    
    # On vérifie que toutes les équipes ont été assignées
    assert np.all(assignations != -1), "Toutes les équipes doivent être assignées à une compétition."
    # que toutes les compétitions ont au plus 24 équipes assignées
    assert np.all(np.bincount(assignations) <= 24), "Aucune compétition ne doit avoir plus de 24 équipes assignées."
    # que toutes les compétitions ont au moins 8 équipes assignées
    assert np.all(np.bincount(assignations) >= 8), "Toutes les compétitions doivent avoir au moins 8 équipes assignées."

    return assignations
