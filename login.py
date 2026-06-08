# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# JCY et Adriano Alves Morais (projet Python) - 2025-2026
# 25 mai 2026
# login.py : affichage de la fenêtre de connexion et d'inscription

import tkinter as tk
from tkinter import messagebox, colorchooser
from model import check_login, check_register, save_register
from utils.session import Session

def show_login(parent, db_mode="local" ):
    if Session.is_authenticated():
        messagebox.showinfo("Info", f"Déjà connecté en tant que {Session.pseudo}")
        return
    win = tk.Toplevel(parent)
    win.title("Login")

    # Empêcher d'interagir avec parent
    win.transient(parent)   # attache au parent
    win.grab_set()          # rend la fenêtre modale


    tk.Label(win, text="Pseudo").grid(row=0, column=0)
    tk.Label(win, text="Mot de passe").grid(row=1, column=0, padx=20, pady=20)

    entry_pseudo = tk.Entry(win)
    entry_pseudo.grid(row=0, column=1)

    entry_pass = tk.Entry(win, show="*")
    entry_pass.grid(row=1, column=1, padx=20, pady=20)

    def attempt_login(db_mode=db_mode):
        user = check_login(entry_pseudo.get(), entry_pass.get(), db_mode)

        if user:
            Session.login(user["pseudo"], user["level"], user["id"])
            messagebox.showinfo("OK", f"Bienvenue {user['pseudo']} !")
            win.destroy()
        else:
            messagebox.showerror("Erreur", "Login incorrect")

    tk.Button(win, text="Se connecter", command=attempt_login).grid(row=2, column=0, columnspan=2)
    
    # Empêche d'accéder à la fenêtre principale tant que login est ouvert
    parent.wait_window(win)

# Affichage de la fenêtre d'enregistrement
def show_register(parent, db_mode="local"):

    win = tk.Toplevel(parent)
    win.title("Register")

    # Empêcher d'interagir avec parent
    win.transient(parent)  # attache au parent
    win.grab_set()  # rend la fenêtre modale

    tk.Label(win, text="Pseudo").grid(row=0, column=0)
    tk.Label(win, text="Mot de passe").grid(row=1, column=0, padx=20, pady=10)
    tk.Label(win, text="Confirmer le mot de passe").grid(row=2, column=0, padx=20, pady=10)
    tk.Label(win, text="Choisir une couleur").grid(row=3, column=0, padx=20, pady=10)

    entry_pseudo = tk.Entry(win)
    entry_pseudo.grid(row=0, column=1)

    entry_pass = tk.Entry(win, show="*")
    entry_pass.grid(row=1, column=1, padx=20, pady=10)

    entry_confirm_pass = tk.Entry(win, show="*")
    entry_confirm_pass.grid(row=2, column=1, padx=20, pady=10)

    default_color = tk.StringVar(value="#FFFFFF") # Couleur par défaut

    # choix des couleurs avec colorchooser
    def choose_color():
        global color

        color = colorchooser.askcolor(title="Choisissez une couleur")[1]

        if color:
            default_color.set(color) # Couleur sélectionnée
            color_button.config(bg=color)
            return color

    color_button = tk.Button(win, text="Couleurs", fg="#000000", bg=default_color.get(), command=choose_color)
    color_button.grid(row=3, column=1)

    # verification des champs et enregistrement de l'utilisateur
    def attempt_register(db_mode=db_mode):

        # obligation de mettre un pseudo et mot de passe valide
        if not entry_pseudo.get() or not entry_pass.get():
            messagebox.showerror("Erreur", "Les champs Pseudo et mot de passe sont obligatoires.")
        elif entry_pass.get() != entry_confirm_pass.get():
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas.")
        else:
            user = check_register(entry_pseudo.get(), db_mode)
            if user:
                messagebox.showerror("Erreur", f"un compte avec le pseudo {user['pseudo']} éxiste déjà.")
            else:
                get_password = entry_pass.get()
                save_register(entry_pseudo.get(), get_password, color, db_mode) # enregistrement dans la db
                messagebox.showinfo("OK", "Enregistrement réussi !")
                win.destroy()

    tk.Button(win, text="S'enregistrer", command=attempt_register).grid(row=4, column=0, columnspan=2)

    # Empêche d'accéder à la fenêtre principale tant que register est ouvert
    parent.wait_window(win)