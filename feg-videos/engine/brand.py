"""Charte graphique FEG : couleurs utilisées par les storyboards (story.py) et le moteur de rendu."""

# Fonds des cartons (dégradé radial : couleur centre, couleur bords)
VERT = ((12, 66, 36), (3, 26, 13))          # vert FEG profond
VERT_VIF = ((14, 84, 46), (4, 34, 18))      # vert FEG plus lumineux
FORET = ((20, 52, 34), (6, 18, 11))         # vert forêt
NOIR_VERT = ((30, 36, 30), (8, 10, 8))      # presque noir, teinté vert
CREME = ((244, 240, 228), (214, 204, 178))  # crème / bronze clair (texte foncé dessus)

# Couleurs de texte
BLANC = (255, 255, 255)
ENCRE = (11, 50, 27)            # vert très foncé, pour les cartons crème
BRONZE = (206, 178, 116)        # mots-clés sur fond foncé
BRONZE_FONCE = (146, 112, 52)   # mots-clés sur fond crème
VERT_LOGO = (11, 61, 32)        # mots-clés verts sur fond crème

# Styles de ligne pour les cartons : (texte, style, taille, couleur)
#   "b"      -> Montserrat Bold (texte courant)
#   "script" -> Anton en MAJUSCULES (mots-clés, le moteur convertit automatiquement)
