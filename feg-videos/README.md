# Vidéos FEG — fabrique de vidéos verticales

Ce dossier transforme **un texte de publication + quelques photos** en vidéo verticale (720×1280, format Reels / TikTok / Shorts / Stories) aux couleurs de la **Fédération des Entreprises du Gabon** :

- titre d'ouverture en bandeaux verts ;
- photos animées (zooms, travellings, transitions rapides) ;
- sous-titres mot à mot, synchronisés sur la voix ;
- cartons typographiques vert / bronze / crème avec les mots-clés ;
- logo FEG en haut à gauche sur tous les plans ;
- voix off naturelle (voix Gemini avec accent gabonais, **ou votre propre voix**) ;
- musique d'ambiance générée (libre de droits) ;
- fin standard : logo, « Pense à t'abonner, liker pour ne rien manquer ! », avec l'icône cloche puis l'icône cœur, synchronisées sur la phrase.

---

## Faire une nouvelle vidéo (ce que VOUS faites)

1. Sur GitHub, ouvrez le dossier `feg-videos/videos/`.
2. Créez un dossier au format `AAAA-MM-JJ_sujet-court` (ex. `2026-12-03_forum-emploi-jeunes`) :
   **Add file → Upload files**, puis glissez :
   - un fichier **`texte.md`** contenant le texte de la publication (copiez `videos/_modele/texte.md`) ;
   - vos **photos** (jpg/png), de préférence en haute définition ; elles iront dans un sous-dossier `photos/`.
     Sur GitHub, tapez le chemin `videos/AAAA-MM-JJ_sujet/photos/` dans le nom de fichier pour créer le sous-dossier.
   - *(optionnel)* votre **enregistrement de voix** (`voix.m4a`, `voix.mp3`…) si vous voulez votre propre voix.
3. Ouvrez une session **Claude Code** sur ce dépôt (environnement « Montage vidéo », qui contient la clé Gemini) et écrivez simplement :

   > Fais la vidéo du dossier `feg-videos/videos/2026-12-03_forum-emploi-jeunes`, voix masculine et féminine.

   Claude écrit le storyboard, génère les voix, vérifie qu'elles n'ont rien inventé, monte la vidéo et vous l'envoie.

Variantes que vous pouvez demander : « sans voix » (musique + textes seulement), « avec ma voix (fichier voix.m4a) », « seulement la voix féminine », « plus court (45 s max) », « sans accent », etc.

### Enregistrer votre voix
Smartphone à ~20 cm, pièce calme, lisez le texte d'une traite, naturellement (les respirations sont bienvenues). En cas d'erreur, marquez une pause et reprenez la phrase. N'importe quel format audio convient.

---

## Fonctionnement technique (pour info)

```
feg-videos/
├── CLAUDE.md              instructions détaillées pour Claude
├── brand/                 logos FEG (blanc, couleur) + polices
├── engine/
│   ├── brand.py           couleurs FEG
│   ├── make_video.py      pipeline complet (voix → contrôle → alignement → rendu → mixage)
│   ├── voice.py           voix Gemini, import de votre enregistrement, transcription de contrôle
│   ├── align.py           calage du montage sur la voix
│   ├── render.py          rendu des images
│   └── music.py           musique générée
└── videos/
    ├── _modele/           modèle à copier (texte.md + story.py commenté)
    └── 2026-11-05_rencontre-FEG-AFD/   exemple complet
```

Commande principale :

```bash
python3 engine/make_video.py videos/<dossier> --voix Achird --tag masculine
```

Prérequis : Python 3, `ffmpeg`, `pip install -r requirements.txt`, et une clé API Gemini
(enregistrée dans les secrets réseau de l'environnement pour `generativelanguage.googleapis.com`, ou variable `GEMINI_API_KEY`).

**Quota gratuit Gemini** : environ 10 générations de voix par jour et par modèle. Une vidéo = 1 génération par voix (+ 1 transcription de contrôle). Pour lever la limite, activez la facturation dans Google AI Studio (quelques centimes par vidéo).

Les vidéos produites (`sortie/`) et les fichiers intermédiaires (`build/`) ne sont pas versionnés : Claude vous les envoie directement.
