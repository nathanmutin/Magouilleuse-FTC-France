import numpy as np
from typing import Tuple

def matrice_voeux_semi_aleatoire(travel_times_matrix: np.ndarray, temperature: float = 2.0) -> np.ndarray:
    """
    Remplissage semi-aléatoire de la matrice des voeux
    La distribution de probabilité du premier choix est donnée par le softmax des temps de trajet,
    et les choix suivants sont faits de manière similaire en retirant les compétitions déjà choisies.
    
    Ainsi, les équipes sont plus susceptibles de choisir les compétitions les plus proches,
    mais il y a une part d'aléatoire qui permet de simuler des choix prenant en compte d'autres facteurs que la distance.
    
    Args:
        travel_times_matrix (np.ndarray): Matrice des temps de trajet entre les équipes et les compétitions (en heures)
        temperature (float): Paramètre de température pour le softmax (contrôle la "concentration" des choix)
        
    Returns:
        np.ndarray: Matrice des rangs de choix (1 pour le premier choix, 2 pour le deuxième, etc.)
    """
    num_equipes, num_compets = travel_times_matrix.shape
    matrice_voeux = np.zeros((num_equipes, num_compets), dtype=int)
    
    # Calcul des probabilités de choix pour chaque équipe et chaque compétition
    # Softmax : la probabilité de choisir une compétition est proportionnelle à exp(-temps_de_trajet/temperature)
    # avec temperature qui contrôle la "concentration" des choix (plus elle est basse, plus les équipes choisiront la compétition la plus proche)
    # On soustrait le max pour éviter les problèmes numériques
    probas = np.exp(-(travel_times_matrix - np.max(travel_times_matrix, axis=1, keepdims=True)) / temperature)
    probas /= probas.sum(axis=1, keepdims=True)
    
    # Pour chaque équipe,
    for i in range(num_equipes):
        # Pour chaque choix (1er, 2e, etc.),
        for choice in range(num_compets):
            # On tire une compétition aléatoire selon les probabilités du softmax
            event_index = np.random.choice(num_compets, p=probas[i])
            # On attribue le rang du choix (1 pour le premier choix, 2 pour le deuxième, etc.)
            matrice_voeux[i, event_index] = choice + 1
            
            if choice < num_compets - 1:  # Si ce n'est pas le dernier choix
                # On retire cette compétition des choix suivants pour éviter les doublons
                probas[i, event_index] = 0
                probas[i] /= probas[i].sum()  # Re-normaliser les probabilités
    
    return matrice_voeux

def matrice_distances_aleatoire(num_equipes: int, num_compets: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Génère une matrice de distances aléatoires entre les équipes et les compétitions.
    
    Args:
        num_equipes (int): Nombre d'équipes
        num_compets (int): Nombre de compétitions
        
    Returns:
        np.ndarray: positions des compétitions
        np.ndarray: positions des équipes
        np.ndarray: Matrice des temps de trajet entre les équipes et les compétitions (en heures)
    """
    # On génère les positions des compétitions de manière aléatoire
    # dans un carré de 8x8 heures (distance = temps de trajet en heures)
    taille_carre = 8
    coordonees_compets = np.random.rand(num_compets, 2) * taille_carre
    
    # On génére les positions des équipes de manière aléatoire
    # en considérant des clusters autour des compétitions
    
    # Variable latente
    proba_cluster = np.random.rand(num_compets+1) + 1
    proba_cluster /= proba_cluster.sum()
    cluster_indices = np.random.choice(num_compets+1, size=num_equipes, p=proba_cluster)
    
    # On génère les coordonnées des équipes en fonction de leur cluster
    # en considérant une distribution normale autour de chaque compétition
    # avec un écart-type entre 0.5 et 1.5 heure
    ecart_types = np.random.rand(num_compets) * 0.5 + 1.
    coordonees_equipes = np.zeros((num_equipes, 2))
    for i in range(num_equipes):
        if cluster_indices[i] == num_compets:  # Cluster "hors compétition"
            coordonees_equipes[i] = np.random.rand(2)*taille_carre  # Position aléatoire dans le carré
        else:
            compet_cluster = cluster_indices[i]
            coordonees_equipes[i] = np.random.normal(loc=coordonees_compets[compet_cluster], scale=ecart_types[compet_cluster], size=2)
    
    # On calcule la matrice des temps de trajet entre les équipes et les compétitions
    # en utilisant la distance euclidienne entre les coordonnées
    distances = np.linalg.norm(coordonees_equipes[:, np.newaxis, :] - coordonees_compets[np.newaxis, :, :], axis=2)
    
    return coordonees_compets, coordonees_equipes, distances

if __name__ == "__main__":
    num_equipes = 155
    num_compets = 7
    
    assert num_equipes >= 8 * num_compets, "Il doit y avoir au moins 8 équipes par compétition pour que l'assignation soit possible."
    assert num_equipes <= 24 * num_compets, "Il doit y avoir au maximum 24 équipes par compétition pour que l'assignation soit possible."
    
    # Genération des positions des compétitions, des équipes, et de la matrice des temps de trajet
    coordonees_compets, coordonees_equipes, matrice_trajets = matrice_distances_aleatoire(num_equipes, num_compets)
    
    # Génération de la matrice des voeux semi-aléatoire
    matrice_voeux = matrice_voeux_semi_aleatoire(matrice_trajets, temperature=2.0)
    
    # Affichage des compétitions et des équipes sur une carte
    # Chaque compétition est représentée par une couleur
    # Le nombre d'équipes inscrites à chaque compétition est indiqué à côté de la compétition
    # Les premiers voeux des équipes sont indiqués par des points de la même couleur
    # Les assignations finales sont indiquées par des cercles autour des équipes
    # Les équipes qui ne sont pas assignées à leur premier choix ont le rang de leur assignation indiqué à côté d'elles
    #
    # 1 subplot pour chaque algorithme d'assignation (linéaire et deferred acceptance) pour comparer les résultats
    import matplotlib.pyplot as plt
    plt.figure(figsize=(15, 7))
    
    for algo in ["Linear Problem", "Deferred Acceptance"]:

        # Calcul de la matrice des coûts et résolution du problème d'affectation
        if algo == "Linear Problem":
            import src.linear_problem
            affectation = src.linear_problem.assign(matrice_voeux, matrice_trajets)
        else:
            import src.deferred_acceptance
            affectation = src.deferred_acceptance.assign(matrice_voeux, matrice_trajets)
        
        plt.subplot(1, 2, 1 if algo == "Linear Problem" else 2)
        colors = plt.get_cmap('tab10', num_compets)
        for j in range(num_compets):
            plt.scatter(coordonees_compets[j, 0], coordonees_compets[j, 1], color=colors(j), marker='s', s=200, label=f'Compétition {j+1}')
            plt.text(coordonees_compets[j, 0], coordonees_compets[j, 1], (affectation == j).sum(), fontsize=12, ha='center', va='center', color='white')
            plt.scatter(coordonees_equipes[matrice_voeux[:, j] == 1, 0], coordonees_equipes[matrice_voeux[:, j] == 1, 1], color=colors(j), alpha=0.5)
            plt.scatter(coordonees_equipes[affectation == j, 0], coordonees_equipes[affectation == j, 1], facecolors='none', edgecolors=colors(j), s=100, label=f'Assignées à Compétition {j+1}')
        for i in range(num_equipes):
            if affectation[i] != np.argmin(matrice_voeux[i]):
                plt.text(coordonees_equipes[i, 0], coordonees_equipes[i, 1], str(matrice_voeux[i, affectation[i]]), fontsize=8, ha='center', va='center')
        
        # Création des entrées de légende personnalisées
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10, label='Compétition'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=8, alpha=0.5, label='Premier choix'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='w', markeredgecolor='gray', markersize=8, label='Assignation finale')
        ]
        plt.legend(handles=legend_elements, loc='best')
        
        plt.title(algo)
        plt.xlabel("Coordonnée X (heures)")
        plt.ylabel("Coordonnée Y (heures)")
        plt.grid(True)

plt.show()
    