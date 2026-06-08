# prototype d'affichage de mindmap en radial et forum
# avec possibilité d'éditer les nodes (si auteur) ou d'en ajouter en dessous    
# JCY et Adriano Alves Morais (projet Python) - 2025-2026 -v1.0
# 25 mai 2026
# main.py : affichage de la fenêtre principale, gestion de la connexion et des différentes vues (tables + mindmaps)

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog, colorchooser
from login import show_login, show_register
from tree_display import display_array
from model import get_maps, get_nodes_for_map, get_users, get_nodes, edit_node_db, delete_node_db, insert_node_db, edit_map_db, delete_map_db, insert_map_db, update_user_profile, get_user_profile, check_login
from utils.session import Session

# Variable globale pour le mode DB
db_mode = None
current_map_id = None

# variable globale pour la vue du frame gauche lors du rafraichissement général
current_left_frame = ""

# Vérification de connexion
def check_auth():
    return Session.is_authenticated()

# affichage des maps 
def display_maps():
    global current_left_frame
    current_left_frame = "maps"

    result = get_maps(db_mode)
    frm_result.tree = display_array(frm_result, result)
    frm_result.tree.bind("<Double-1>", on_map_double_click) # double clic pour afficher le mindmap dans right_frame selon le mode sélectionné (tree, radial ou forum)
    frm_result.tree.bind("<Button-3>", maps_menu) # Clic droit pour afficher le menu d'édition de map

# affichage des users
def display_users():
    global current_left_frame
    current_left_frame = "users"

    result = get_users(db_mode)

    frm_result.tree = display_array(frm_result, result)

# affichage des nodes
def display_nodes():
    global current_left_frame
    current_left_frame = "nodes"

    result = get_nodes(db_mode)

    # remplace les valeurs none par -1 pour éviter les erreurs
    for node in result:
        if node["parent_id"] is None:
            node["parent_id"] = 0

    frm_result.tree = display_array(frm_result, result)

# traitement de l'affichage d'un mindmap selon le mode sélectionné (tree, radial ou forum)
def on_map_double_click(event):
    selected = frm_result.tree.selection()
    if selected:
        item = frm_result.tree.item(selected[0])
        values = item['values']
        map_id = values[0]  # Supposons que id est la première colonne
        display_mindmap(map_id)

# affichage du mindmap selon le mode sélectionné
def display_mindmap(map_id):
    global current_map_id
    current_map_id = map_id
    nodes = get_nodes_for_map(map_id,db_mode)
    # Nettoyer right_frame
    for widget in right_frame.winfo_children():
        widget.destroy()
    # Afficher les nodes selon le mode
    if nodes:
        mode = display_mode.get()
        if mode == 'tree':
            display_mindmap_tree(right_frame, nodes)
        elif mode == 'forum':
            display_mindmap_forum(right_frame, nodes)
        elif mode == 'organigramme':
            display_mindmap_organigramme(right_frame, nodes)
    else:
        tk.Label(right_frame, text="Aucun node pour ce mindmap").pack()

# Rafraichit le mindmap
def refresh_mindmap():
    if current_map_id is not None:
        display_mindmap(current_map_id)

# Rafraichit tout : le mindmap et la liste des maps, users ou nodes selon ce qui est affiché dans left_frame
def refresh_all():
    refresh_mindmap()

    if current_left_frame == "nodes":
        display_nodes()
    elif current_left_frame == "users":
        display_users()
    elif current_left_frame == "maps":
        display_maps()

# Affichage du mindmap en TreeView (version simple)
def display_mindmap_tree(frame, nodes):

    # Créer le Treeview
    tree = ttk.Treeview(frame, columns=(), show='tree')  # Pas de colonnes supplémentaires
    tree.heading('#0', text='Text')

    # Police plus petite et interligne ajusté pour beaucoup d'enregistrements
    style = ttk.Style()
    style.configure("Right.Treeview", font=("TkDefaultFont", 20), rowheight=35)
    tree.configure(style="Right.Treeview")

    # Fonction récursive pour insérer les nodes
    def insert_nodes(parent, parent_id=None, level=0):
        for node in nodes:
            if node['parent_id'] == parent_id:

                # Récupère la couleur de l'auteur du node sauf si le level est 0 (couleur par défaut du titre des maps)
                if level == 0:
                    color = "lightblue"
                else:
                    color = node.get("color", "black")
                # Crée un nom de tag unique pour l'utilisateur
                tag_name = f"user_color_{color}"
                # Configure le tag : le texte de la ligne aura cette couleur
                tree.tag_configure(tag_name, foreground=color)

                item = tree.insert(parent, 'end', text=node['text'],tags=(tag_name,))  # Seulement le text (ajout du tags pour la couleur de la ligne)
                insert_nodes(item, node['id'], level + 1) # Ajout de level + 1 pour séparer la couleur du titre d'un node avec les autres

    insert_nodes('')

    # Scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')

    # Donne le focus au canvas pour permettre le scroll avec la molette, lorsque la souris le survole.
    tree.bind("<Enter>", lambda e: tree.focus_set())

    # Scroll vertical
    tree.bind("<MouseWheel>", lambda e: tree.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    tree.bind("<Shift-MouseWheel>", lambda e: tree.xview_scroll(int(-1 * (e.delta / 120)), "units"))


# Affichage du mindmap en forum (version plus compacte et adaptée à l'affichage de nombreux nodes, avec possibilité d'éditer les nodes ou d'en ajouter en dessous)
def display_mindmap_forum(frame, nodes):
    container = tk.Frame(frame)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, bg='white')
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Donne le focus au canvas pour permettre le scroll avec la molette, lorsque la souris le survole.
    canvas.bind("<Enter>", lambda e: canvas.focus_set())

    # Scroll vertical
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Mise à jour de la zone scrollable
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", update_scroll_region)

    # Trouver le root
    root_node = next((n for n in nodes if n['parent_id'] is None or n['parent_id'] == 0), None)
    if not root_node:
        return

    canvas_width = 800
    canvas_height = 600
    node_height = 25  # Réduit à 30 pour moins de place verticale

    # Crée un rectangle arrondi (pour les nodes du forum)
    def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=10, **kwargs):

        # sécurité : éviter un rayon trop grand
        radius = min(radius, abs(x2 - x1)//2, abs(y2 - y1)//2)

        points = [ x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
            x1 + radius, y1 ]

        return canvas.create_polygon(points, smooth=True, **kwargs)

    # Place les nodes en mode forum de manière récursive
    def place_forum(node, x, y, width_percent, level=0):
        width = int(canvas_width * width_percent / 100)
        item = create_rounded_rectangle(canvas, x, y, x + width, y + node_height, radius=8, fill='lightblue' if level == 0 else node["color"], outline='black')
        canvas.create_text(x + width/2, y + node_height/2, text=node['text'][:40], anchor='center', font=("Arial", 12))  # Police augmentée

        # Binder le clic droit sur le node pour éditer
        canvas.tag_bind(item, "<Button-3>", lambda e, n=node: edit_node(e, n)) # n contient les infos du node pour l'édition    
        children = [n for n in nodes if n['parent_id'] == node['id']]
        total_height = node_height + 10  # hauteur du node + marge

        if children:
            child_x = x + int(canvas_width * 20 / 100)  # décalage de 20%
            child_width_percent = max(width_percent - 5, 10)  # diminuer de 5% par niveau, min 10%
            current_y = y + node_height + 10
            for child in children:
                child_height = place_forum(child, child_x, current_y, child_width_percent, level+1)
                current_y += child_height
                total_height += child_height
        return total_height

    place_forum(root_node, 20, 20, 50) # le root prend 50% de la largeur, les enfants 45%, etc. 
    update_scroll_region()

# Affichage des mindmaps en mode organigramme
def display_mindmap_organigramme(frame, nodes):
    container = tk.Frame(frame)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, bg='white')
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Donne le focus au canvas pour permettre le scroll avec la molette
    canvas.bind("<Enter>", lambda e: canvas.focus_set())

    # Scroll vertical
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Mise à jour de la zone scrollable
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", update_scroll_region)

    # Trouver le root
    root_node = next((n for n in nodes if n['parent_id'] is None or n['parent_id'] == 0), None)
    if not root_node:
        return

    # longueur du canvas
    canvas_width = 800

    # taille des nodes
    node_width = 100 # longueur
    node_height = 50 # largeur

    # espacement entre les nodes
    gap_x = 40 # horizontal
    gap_y = 80 # vertical

    # Crée un rectangle arrondi
    def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=10, **kwargs):
        radius = min(radius, abs(x2 - x1)//2, abs(y2 - y1)//2) # calcul du radius

        # différents points qui composent le rectangle arrondi (comme pour la vue forum)
        points = [
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
            x1 + radius, y1
        ]

        return canvas.create_polygon(points, smooth=True, **kwargs)

    # Récupère les enfants directs d'un node
    def get_children(node):
        return [n for n in nodes if n['parent_id'] == node['id']]

    # Compte combien de place une branche doit prendre
    def count_width(node):
        total_width = 0 # longueur totale du node et ses enfants

        children = get_children(node) # récupère tout les enfants du node

        # si pas d'enfant, on retourne simplement le node parent avec le gap horizontal
        if not children:
            return node_width + gap_x

        # calcul la longueur total que prendra un node et ses enfants (récursif)
        for child in children:
            total_width += count_width(child)

        return total_width

    # Crée visuellement un node
    def create_node(node, x, y, level=0):
        color = 'lightblue' if level == 0 else node.get("color", "white")

        # créer le rectangle du node
        item = create_rounded_rectangle(
            canvas,
            x,
            y,
            x + node_width,
            y + node_height,
            radius=10,
            fill=color,
            outline='black'
        )

        # créer le texte du node
        canvas.create_text(
            x + node_width / 2,
            y + node_height / 2,
            text=node['text'][:28], #maximum 28 caractères pour ne pas dépasser du rectangle
            anchor='center',
            font=("Arial", 10),
            width=node_width - 10
        )

        # Clic droit sur le node
        canvas.tag_bind(item, "<Button-3>", lambda e, n=node: edit_node(e, n)) # n contient les infos du node pour l'édition

    # Place les nodes en organigramme de manière récursive
    def place_organigramme(node, x, y, level=0):
        create_node(node, x, y, level) # création du node

        children = get_children(node) # récupère tout les enfants du node

        # si pas d'enfant retourne juste le parent
        if not children:
            return count_width(node)

        total_width = count_width(node) # longeur total d'un node et ses enfants

        child_posy = y + node_height + gap_y # calcul de la position en Y des enfants avec un espace entre eux
        current_posx = x - total_width / 2 + node_width / 2 # calcul de la position actuel en X du node

        for child in children:
            child_width = count_width(child) # longueur de l'enfant

            child_posx = current_posx + child_width / 2 - node_width / 2 # calcul de la position en X de l'enfant

            # Ligne parent → enfant
            canvas.create_line(
                x + node_width / 2,
                y + node_height,
                child_posx + node_width / 2,
                child_posy,
                fill='gray',
                width=1
            )

            place_organigramme(child, child_posx, child_posy, level + 1)

            current_posx += child_width

        return total_width

    # Placement du root au centre en haut
    place_organigramme(root_node, canvas_width / 2 - node_width / 2, 40)

    update_scroll_region()

# Cette fonction propose 3 actions sur un node : éditer le texte, supprimer le node ou insérer un nouveau node en dessous
def edit_node(event, node):
    if not check_auth():
        messagebox.showerror("Erreur", "Vous devez être connecté pour éditer un node.")
        return
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Éditer", command=lambda: edit_text(node))
    menu.add_command(label="Supprimer", command=lambda: delete_node_action(node))
    menu.add_command(label="Insérer en dessous", command=lambda: insert_below(node))
    menu.post(event.x_root, event.y_root)

# propose d'éditer le texte d'un node (seulement si l'utilisateur est l'auteur du node)
def edit_text(node):
    # vérifier que l'utilisateur est l'auteur du node
    if Session.id != node["author_id"]:
        messagebox.showerror("Erreur", "Vous n'êtes pas propriétaire du node")
        return

    text_modif = simpledialog.askstring("Éditer le node", "Nouveau texte:", initialvalue=node["text"], parent=root)

    # text_modif ne dois pas etre null
    if text_modif:
        edit_node_db(text_modif, node["id"], db_mode)

    # rafraichis la mindmap
    refresh_mindmap()

# propose de supprimer un node (seulement si l'utilisateur est l'auteur du node)
def delete_node_action(node):
    # vérifier que l'utilisateur est l'auteur du node
    if Session.id != node["author_id"]:
        messagebox.showerror("Erreur", "Vous n'êtes pas propriétaire du node")
        return

    # message d'avertissement avant suppression
    if messagebox.askyesno("Confirmer la suppression", "Êtes-vous sûr de vouloir supprimer ce node ? Cette action est irréversible."):
        delete_node_db(node["id"], db_mode)

        # Supprime la map si on supprime le node principal
        if node["parent_id"] is None:
            delete_map_db(node["map_id"], db_mode)

            # Rafraîchit la liste des maps
            display_maps()

    # rafraichis la mindmap
    refresh_mindmap()

# propose d'insérer un nouveau node en dessous du node sélectionné (le nouveau node aura comme parent le node sélectionné)
def insert_below(node):
    #demande le texte du node
    text_insert = simpledialog.askstring("Insérer un node", "Nouveau texte:", parent=root)

    # text_insert ne dois pas etre null
    if text_insert:
        insert_node_db(current_map_id, node["id"], Session.id, text_insert, node["level"], db_mode)

    # rafraichis la mindmap
    refresh_mindmap()

# Menu d'édition des maps avec le clique droit
def maps_menu(event):
    # Récupère la ligne sur laquelle on a fait clic droit. event.y est la position y de la souris sur la frame
    selected_item = frm_result.tree.identify_row(event.y)

    # Si on clique dans le vide, on ne fait rien
    if not selected_item:
        return

    # Vérifie que l'utilisateur est connecté
    if not check_auth():
        messagebox.showerror("Erreur", "Vous devez être connecté pour éditer une map.")
        return

    # Sélectionne visuellement la ligne cliquée
    frm_result.tree.selection_set(selected_item)

    # Récupère les valeurs de la ligne
    item = frm_result.tree.item(selected_item)
    values = item["values"]

    # get_maps retourne : id, title, author_id, level
    map_data = {
        "id": values[0],
        "title": values[1],
        "author_id": values[2],
    }

    # Création du menu clic droit
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Éditer", command=lambda: edit_map(map_data))
    menu.add_command(label="Supprimer", command=lambda: delete_map(map_data))
    menu.add_command(label="Insérer en dessous", command=lambda: insert_map())
    menu.post(event.x_root, event.y_root)

# Edition de la map sélectionnée
def edit_map(map_data):
    # Vérifie que l'utilisateur est l'auteur de la map ou admin
    if Session.id != map_data["author_id"] and Session.level != 2:
        messagebox.showerror("Erreur", "Vous n'êtes pas propriétaire de cette map.")
        return

    # Demande le nouveau titre
    new_title = simpledialog.askstring(
        "Éditer la map",
        "Nouveau titre :",
        initialvalue=map_data["title"],
        parent=root
    )

    # Si l'utilisateur annule ou laisse vide, on ne fait rien
    if not new_title:
        return

    # Mise à jour en base de données
    edit_map_db(new_title, map_data["id"], db_mode)

    # Rafraîchit la liste des maps
    display_maps()

# Edition de la map sélectionnée
def delete_map(map_data):

    # Vérifie que l'utilisateur est l'auteur de la map ou admin
    if Session.id != map_data["author_id"] and Session.level != 2:
        messagebox.showerror("Erreur", "Vous n'êtes pas propriétaire de cette map.")
        return

    # message d'avertissement avant suppression
    if messagebox.askyesno("Confirmer la suppression","Êtes-vous sûr de vouloir supprimer cette map ? Cette action est irréversible."):
        # verifier qu'il n'y a pas de node dans la map à supprimer
        try:
            delete_map_db(map_data["id"], db_mode)
        except:
            messagebox.showerror("Erreur", "Vous devez d'abord supprimer le node principal.")

    # Rafraîchit la liste des maps
    display_maps()

def insert_map():
    #demande le texte du node
    text_insert = simpledialog.askstring("Insérer une map", "Nouveau texte:", parent=root)

    # text_insert ne dois pas etre null
    if text_insert:
        new_map_id = insert_map_db(text_insert, Session.id, db_mode)
        insert_node_db(new_map_id, None, Session.id, text_insert, -1, db_mode) # -1 pour le level 0 du node

    # Rafraîchit la liste des maps
    display_maps()

# Permet de changer le mode de la base de données (local ou remote) et met à jour la variable globale db_mode
def set_db_mode(mode):
    global db_mode
    if mode != db_mode: # éviter de faire un logout inutile qui ferait perdre la connexion à l'utilisateur
        db_mode = mode
        Session.logout()  # forcer le logout pour éviter les incohérences
        lbl_user.config(text="Non connecté")
        lbl_db_mode.config(text=f"Mode DB: {db_mode}", bg="red" if db_mode == "remote" else "green", fg="white")
        display_maps()  # rafraîchir l'affichage des maps pour éviter les incohérences

# connexion (appelle une fenêtre de login)
def login():
    show_login(root, db_mode)
    if Session.is_authenticated():
        lbl_user.config(text=f"Connecté en tant que {Session.pseudo}/{Session.level}")

# déconnexion
def logout():
    if Session.is_unauthenticated():
        messagebox.showinfo("Info", "Vous n'êtes pas connecté")
    else:
        Session.logout()
        lbl_user.config(text="Non connecté")

# enregistrement (appelle une fenêtre d'enregistrement)
def register():
    show_register(root, db_mode)

# edition de son profile utilisateur
def edit_profile(parent, db_mode="local"):
    # Vérifie que l'utilisateur est connecté
    if not check_auth():
        messagebox.showerror("Erreur", "Vous devez être connecté pour modifier votre profil.")
        return

    # Récupère les informations du profil
    result = get_user_profile(Session.id, db_mode)

    # stock l'utilisateur seul
    user = result[0]

    win = tk.Toplevel(parent)
    win.title("Profile")

    # Empêcher d'interagir avec la fenêtre principale
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="Pseudo").grid(row=0, column=0, padx=20, pady=10)
    tk.Label(win, text="Mot de passe actuel").grid(row=1, column=0, padx=20, pady=10)
    tk.Label(win, text="Nouveau mot de passe").grid(row=2, column=0, padx=20, pady=10)
    tk.Label(win, text="Confirmer le nouveau mot de passe").grid(row=3, column=0, padx=20, pady=10)
    tk.Label(win, text="Couleur").grid(row=4, column=0, padx=20, pady=10)

    entry_pseudo = tk.Entry(win)
    entry_pseudo.grid(row=0, column=1, padx=20, pady=10)

    # Insère le pseudo actuel dans le champ
    entry_pseudo.insert(0, user["pseudo"])

    entry_current_password = tk.Entry(win, show="*")
    entry_current_password.grid(row=1, column=1, padx=20, pady=10)

    entry_new_password = tk.Entry(win, show="*")
    entry_new_password.grid(row=2, column=1, padx=20, pady=10)

    entry_confirm_password = tk.Entry(win, show="*")
    entry_confirm_password.grid(row=3, column=1, padx=20, pady=10)

    # Couleur actuelle de l'utilisateur
    selected_color = tk.StringVar(value=user["color"])

    def choose_color():
        color = colorchooser.askcolor(
            title="Choisissez une couleur",
            initialcolor=selected_color.get()
        )[1]

        if color:
            selected_color.set(color)
            color_button.config(bg=color)

    color_button = tk.Button(
        win,
        text="Choisir une couleur",
        fg="#000000",
        bg=selected_color.get(),
        command=choose_color
    )
    color_button.grid(row=4, column=1, padx=20, pady=10)

    def save_profile():
        old_pseudo = user["pseudo"]
        new_pseudo = entry_pseudo.get()
        new_color = selected_color.get()
        current_password = entry_current_password.get()
        new_password = entry_new_password.get()
        new_confirm_password = entry_confirm_password.get()

        if not new_pseudo:
            messagebox.showerror("Erreur", "Le pseudo est obligatoire.")
            return

        if check_login(old_pseudo, current_password, db_mode):
            if new_password != new_confirm_password:
                messagebox.showerror("Erreur", "Les nouveaux mots de passe ne correspondent pas.")
                return
            elif not new_password or not new_confirm_password:
                messagebox.showerror("Erreur", "Les nouveaux mots de passe sont vides")
                return
        elif not current_password:
            if new_password:
                messagebox.showerror("Erreur", "Le mot de passe actuel est requis pour changer le mot de passe.")
                return
            new_password = None  # Pas de changement de mot de passe
        else:
            messagebox.showerror("Erreur", "Les champs ne correspondent pas.")
            return

        update_user_profile(Session.id, new_pseudo, new_color, new_password, db_mode)

        # Met à jour aussi la session actuelle
        Session.pseudo = new_pseudo

        lbl_user.config(text=f"Connecté en tant que {Session.pseudo}/{Session.level}")

        messagebox.showinfo("OK", "Profil modifié avec succès.")
        win.destroy()

        # Rafraîchit la mindmap affichée pour mettre à jour les couleurs
        refresh_mindmap()

    tk.Button(
        win,
        text="Enregistrer",
        command=save_profile
    ).grid(row=5, column=0, columnspan=2, pady=15)

    parent.wait_window(win)

# fenêtre principale
root = tk.Tk()

root.minsize(1200, 800)  # Ajusté pour accommoder les deux frames
root.title("Mindmaps - Version 1.0")

root.bind("<F5>", lambda e: refresh_all())  # F5 pour rafraîchir tout

# Création du menu
menubar = tk.Menu(root)

# Menu Afficher
display_menu = tk.Menu(menubar, tearoff=0)
display_menu.add_command(label="Users", command=display_users) # Afficher users
display_menu.add_command(label="Maps", command=display_maps)
display_menu.add_command(label="Nodes", command=display_nodes) # Afficher nodes
menubar.add_cascade(label="Afficher", menu=display_menu)

# Menu Login/Register
login_menu = tk.Menu(menubar, tearoff=0)
login_menu.add_command(label="Login", command=login)
login_menu.add_command(label="Logout", command=logout) # Menu Logout
login_menu.add_command(label="Register", command=register) # Menu Register
menubar.add_cascade(label="Login/Register", menu=login_menu)

# Menu local/remote
db_menu = tk.Menu(menubar, tearoff=0)
db_menu.add_command(label="Local", command=lambda: set_db_mode('local'))
db_menu.add_command(label="Remote", command=lambda: set_db_mode('remote'))
menubar.add_cascade(label="Mode DB", menu=db_menu)

# Menu profile
menubar.add_command(label="Profile", command=lambda: edit_profile(root, db_mode))

root.config(menu=menubar)

# Configuration du grid pour root
root.columnconfigure(0, minsize=500)  # Frame gauche de largeur fixe 500
root.columnconfigure(1, weight=1)     # Frame droite prend le reste
root.rowconfigure(0, weight=1)

# Frame gauche pour contrôles et affichage des tables
left_frame = tk.Frame(root, bg="lightgray", width=500)
left_frame.grid(column=0, row=0, sticky="ns")  # "ns" pour étirement vertical seulement

# Frame droite pour l'affichage du mindmap
right_frame = tk.Frame(root, bg="white")
right_frame.grid(column=1, row=0, sticky="nsew")

# Variable pour le mode d'affichage
display_mode = tk.StringVar(value='tree')

# Configuration du grid pour left_frame
left_frame.rowconfigure(3, weight=1)  # frm_result prend l'espace restant
left_frame.columnconfigure(0, weight=1)
left_frame.columnconfigure(1, weight=1)

# Information sur la connexion dans left_frame
lbl_user = tk.Label(left_frame, text="Non connecté")
lbl_user.grid(column=0, row=0, padx=10, pady=10)
# Information sur la base de données utilisée 
lbl_db_mode = tk.Label(left_frame, text="db_mode: local")
lbl_db_mode.grid(column=1, row=0, padx=10, pady=10)

# frame pour les boutons dans left_frame
frm_buttons = tk.Frame(left_frame, bg="lightblue")
frm_buttons.grid(column=0, row=1, pady=10)

# frame pour les options d'affichage
frm_options = tk.Frame(left_frame, bg="#f0f0f0")
frm_options.grid(column=0, row=2, pady=10)

tk.Label(frm_options, text="Mode d'affichage Mindmap:").pack(anchor='w')
tk.Radiobutton(frm_options, text="Treeview", variable=display_mode, value='tree', command=refresh_mindmap).pack(anchor='w')
tk.Radiobutton(frm_options, text="Forum", variable=display_mode, value='forum', command=refresh_mindmap).pack(anchor='w')
# Radio bouton pour l'affichage organigramme
tk.Radiobutton(frm_options, text="Organigramme", variable=display_mode, value='organigramme', command=refresh_mindmap).pack(anchor='w')

# frame pour l'affichage des résultats dans left_frame
frm_result = tk.Frame(left_frame, bg="lightgreen")
frm_result.grid(column=0, row=3, columnspan=2, sticky="nsew", padx=10, pady=10)

# Placeholder pour le mindmap dans right_frame
tk.Label(right_frame, text="Zone Mindmap", font=("Arial", 16)).pack(expand=True)

# remplissage de frm_result
tk.Label(frm_result,text="RESULTS").pack()

# Affiche les maps au démarrage
set_db_mode("local")
display_maps()
root.mainloop()


