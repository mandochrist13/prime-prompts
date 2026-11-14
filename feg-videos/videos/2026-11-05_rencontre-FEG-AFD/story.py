# Storyboard : Rencontre FEG – AFD (5 novembre 2026)
# Voir CLAUDE.md pour les règles d'écriture d'un storyboard.
from brand import *

# Photos disponibles (identifiant -> fichier dans photos/)
PHOTOS = {1: "1.jpg", 2: "2.jpg", 3: "3.jpg", 4: "4.jpg"}

# kind = "title" | "photo" | "card" | "end"
# photo : chunks = [(sous-titre affiché, texte prononcé), ...]
# pan = (centre x début, centre x fin, zoom début, zoom fin) ; cy = centre vertical (0..1)
story = [
    dict(kind="title", pid=2, pan=(0.2, 0.6, 1.0, 1.15),
         say="Retour sur la rencontre entre la Fédération des Entreprises du Gabon, et l'Agence Française de Développement.",
         lines=[("Rencontre FEG – AFD", 66), ("La voix du secteur privé", 56), ("face aux partenaires", 56), ("au développement", 56)]),
    dict(kind="photo", pid=4, pan=(0.35, 0.6, 1.05, 1.18), chunks=[
        ("Ce jeudi 5 novembre 2026,", "Ce jeudi, cinq novembre deux mille vingt-six,"),
        ("au siège de la FEG,", "au siège de la Fègue,")]),
    dict(kind="card", c1=VERT[0], c2=VERT[1], say="les membres du Bureau exécutif ont reçu",
         lines=[("les membres du", "b", 64, BLANC), ("Bureau", "script", 160, BRONZE), ("Exécutif", "script", 160, BRONZE), ("ont reçu", "b", 64, BLANC)]),
    dict(kind="photo", pid=3, pan=(0.75, 0.45, 1.0, 1.1), chunks=[
        ("la délégation de l'Agence Française de Développement,", "la délégation de l'Agence Française de Développement,"),
        ("en mission de suivi macroéconomique", "en mission de suivi macro-économique"),
        ("au Gabon du 2 au 6 novembre.", "au Gabon, du deux au six novembre.")]),
    dict(kind="card", c1=CREME[0], c2=CREME[1], grain=14, say="Au cœur des échanges : la voix du secteur privé",
         lines=[("Au cœur", "b", 80, ENCRE), ("des échanges,", "b", 80, ENCRE), ("la voix du", "script", 110, ENCRE), ("secteur", "script", 160, BRONZE_FONCE), ("privé", "script", 160, BRONZE_FONCE)]),
    dict(kind="photo", pid=1, pan=(0.4, 0.6, 1.0, 1.12), chunks=[
        ("sur la situation économique du pays.", "sur la situation économique du pays.")]),
    dict(kind="card", c1=FORET[0], c2=FORET[1], say="L'impact de la dette intérieure sur la trésorerie, l'emploi et l'investissement des entreprises.",
         lines=[("L'impact de la", "b", 64, BLANC), ("dette", "script", 170, BRONZE), ("intérieure", "script", 150, BRONZE),
                ("sur la trésorerie,", "b", 54, BLANC), ("l'emploi et", "b", 54, BLANC), ("l'investissement", "b", 54, BLANC)]),
    dict(kind="photo", pid=2, pan=(0.12, 0.3, 1.3, 1.45), cy=0.55, chunks=[
        ("L'accès des entreprises locales", "L'accès des entreprises locales"),
        ("aux marchés et aux financements des bailleurs.", "aux marchés, et aux financements des bailleurs.")]),
    dict(kind="card", c1=NOIR_VERT[0], c2=NOIR_VERT[1], say="La stabilité juridique et fiscale, gage d'attractivité.",
         lines=[("La", "b", 64, BLANC), ("stabilité", "script", 160, BRONZE), ("juridique", "b", 70, BLANC), ("et fiscale,", "b", 70, BLANC),
                ("gage d'", "b", 56, BLANC), ("attractivité", "script", 140, BRONZE)]),
    dict(kind="photo", pid=3, pan=(0.25, 0.45, 1.15, 1.3), chunks=[
        ("La formation, l'employabilité des jeunes", "La formation, l'employabilité des jeunes,"),
        ("et le contenu local.", "et le contenu local.")]),
    dict(kind="card", c1=CREME[0], c2=CREME[1], grain=14, say="Le financement des opérateurs nationaux des secteurs stratégiques.",
         lines=[("Le financement", "b", 70, ENCRE), ("des opérateurs", "b", 70, ENCRE), ("nationaux", "script", 150, VERT_LOGO),
                ("des secteurs", "b", 70, ENCRE), ("stratégiques", "script", 140, VERT_LOGO)]),
    dict(kind="photo", pid=4, pan=(0.42, 0.5, 1.35, 1.5), cy=0.5, chunks=[
        ("Pour la FEG, les entreprises sont", "Pour la Fègue, les entreprises sont"),
        ("le principal moteur de la croissance", "le principal moteur de la croissance")]),
    dict(kind="card", c1=VERT_VIF[0], c2=VERT_VIF[1], say="et de la diversification de l'économie gabonaise.",
         lines=[("et de la", "b", 70, BLANC), ("diversification", "script", 130, BRONZE), ("de l'économie", "b", 70, BLANC), ("gabonaise", "script", 160, BRONZE)]),
    dict(kind="photo", pid=1, pan=(0.6, 0.35, 1.08, 1.2), chunks=[
        ("Un dialogue franc et constructif", "Un dialogue franc et constructif"),
        ("avec les partenaires au développement", "avec les partenaires au développement")]),
    dict(kind="card", c1=VERT[0], c2=VERT[1], say="reste essentiel.",
         lines=[("reste", "b", 84, BLANC), ("essentiel.", "script", 180, BRONZE)]),
    # Écran de fin standard FEG (ne pas modifier la phrase : la cloche et le cœur se calent dessus)
    dict(kind="end", pid=4, pan=(0.3, 0.7, 1.0, 1.08),
         say="La Fègue, le secteur privé en action. Pense à t'abonner et à liker, pour ne rien manquer !"),
]
