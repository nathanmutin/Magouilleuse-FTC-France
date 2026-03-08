import numpy as np
import pandas as pd

"""
Ce script permet de charger les données des choix des équipes et des temps de trajet,
et de résoudre le problème d'affectation avec deux algorithmes
"""
choix_df = pd.read_csv("choix.csv")

num_equipes = choix_df.shape[0]
compets = np.array(list(
    set(choix_df['Choix 1'].dropna().unique()) |
    set(choix_df['Choix 2'].dropna().unique()) |
    set(choix_df['Choix 3'].dropna().unique()) |
    set(choix_df['Choix 4'].dropna().unique()) |
    set(choix_df['Choix 5'].dropna().unique()) |
    set(choix_df['Choix 6'].dropna().unique())
    ))
num_compets = len(compets)

voeux = np.zeros((num_equipes, num_compets), dtype=int)
for i in range(num_equipes):
    for j in range(1, num_compets + 1):
        choix_j = choix_df.loc[i, f'Choix {j}']
        if pd.notna(choix_j):
            comp_index = np.where(compets == choix_j)[0][0]
            voeux[i, comp_index] = j

"""
S'il faut recalculer les temps de trajet, on peut utiliser le code suivant.
Attention, cela peut prendre plusieurs minutes à exécuter
"""
RECALCUL_TEMPS_TRAJET = False
if RECALCUL_TEMPS_TRAJET:
    ## Calculs des temps de trajet entre les équipes et les compétitions
    from src.temps_trajet import temps_trajet_matrice

    # Villes des équipes (Ville, Département, Région)
    addresses_equipes = (choix_df['Ville'] + ", " + choix_df['Département'] + ", " + choix_df['Région']).tolist()
    # Adresses des compétitions (Région)
    addresses_compets = compets
    addresses_compets = [addr.replace("Neuville", "Neuville-sur-Saône, Rhône") for addr in addresses_compets]
    addresses_compets = [addr.replace("Clermont", "Clermont-Ferrand, Puy-de-Dôme") for addr in addresses_compets]
    addresses_compets = [addr.replace("Valence", "Valence, Drôme") for addr in addresses_compets]
    addresses_compets = [addr.replace("Marnaz", "Marnaz, Haute-Savoie") for addr in addresses_compets]
    addresses_compets = [addr.replace("Paris", "Paris, Ile-de-France") for addr in addresses_compets]

    # Calcul de la matrice des temps de trajet
    temps_trajet = temps_trajet_matrice(addresses_equipes, addresses_compets)

    # Save the travel times matrix to a CSV file
    temps_trajet_df = pd.DataFrame(temps_trajet, index=choix_df['Numéro d\'équipe'], columns=compets)
    temps_trajet_df.to_csv("temps_trajet.csv")

"""
Sinon on peut les charger depuis le fichier CSV
"""
temps_trajet_df = pd.read_csv("temps_trajet.csv", index_col=0)
temps_trajet_matrix = temps_trajet_df.values / 3600  # Convertir les temps de trajet en heures


"""
Résolution des problèmes d'affectation avec les deux algorithmes
"""
import src.linear_problem
solution_1 = src.linear_problem.assign(voeux, temps_trajet_matrix)
import src.deferred_acceptance
solution_2 = src.deferred_acceptance.assign(voeux, temps_trajet_matrix)

# Save the solutions to CSV file
# Copie de choix_df
resultat_df = choix_df.copy()
# Ajout des colonnes d'affectation pour les deux algorithmes
# Il faut mapper le nom de la compétition à l'index de la compétition dans compets pour trouver l'affectation
resultat_df['Affectation Algo 1'] = compets[solution_1]
resultat_df['Affectation Algo 2'] = compets[solution_2]
# Sauvegarde du résultat
resultat_df.to_csv("resultats.csv", index=False)

print("Résultats sauvegardés dans resultats.csv")