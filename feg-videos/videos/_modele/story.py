# Storyboard (modèle). Claude le remplit à partir de texte.md — voir ../../CLAUDE.md.
from brand import *

# Photos du dossier photos/ : identifiant -> nom de fichier
PHOTOS = {1: "1.jpg", 2: "2.jpg"}

story = [
    # Titre : bandeaux verts sur une photo
    dict(kind="title", pid=1, pan=(0.2, 0.6, 1.0, 1.15),
         say="Phrase d'accroche prononcée sur le titre.",
         lines=[("TITRE COURT", 66), ("sous-titre ligne 1", 56), ("sous-titre ligne 2", 56)]),
    # Plan photo : sous-titres (affiché, prononcé) — nombres en lettres et « Fègue » dans le prononcé
    dict(kind="photo", pid=2, pan=(0.35, 0.6, 1.05, 1.18), chunks=[
        ("Ce mardi 3 décembre,", "Ce mardi, trois décembre,"),
        ("au siège de la FEG,", "au siège de la Fègue,")]),
    # Carton typographique : (texte, "b" ou "script", taille, couleur)
    dict(kind="card", c1=VERT[0], c2=VERT[1], say="texte prononcé pendant le carton",
         lines=[("texte courant", "b", 64, BLANC), ("Mot-clé", "script", 160, BRONZE)]),
    # Fin standard (ne pas modifier la phrase)
    dict(kind="end", pid=1, pan=(0.3, 0.7, 1.0, 1.08),
         say="La Fègue, le secteur privé en action. Pense à t'abonner et à liker, pour ne rien manquer !"),
]
