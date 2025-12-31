import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

DB_NAME = "CTPB.db"

def get_user_by_card(card_id):
    """Checks if a user exists in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE card_id = ?", (card_id,))
    user = cursor.fetchone()
    conn.close()
    return user

class UserRegistrationWindow(tk.Toplevel):
    def __init__(self, parent, card_id):
        super().__init__(parent)
        self.title("Registrar Novo Sócio")
        self.geometry("400x500")
        self.card_id = card_id

        # Title
        tk.Label(self, text=f"Novo Cartão: {card_id}", font=("Arial", 10, "bold"), fg="blue").pack(pady=10)

        # Form Fields
        self.entries = {}
        fields = [
            ("Nome", "first_name"),
            ("Apelido", "last_name"),
            ("Email", "email"),
            ("Telemóvel", "phone"),
            ("NIF", "nif"),
            ("Quota Mensal (€)", "monthly_fee")
        ]

        for label_text, key in fields:
            frame = tk.Frame(self)
            frame.pack(fill="x", padx=20, pady=5)
            tk.Label(frame, text=label_text, width=15, anchor="w").pack(side="left")
            entry = tk.Entry(frame)
            entry.pack(side="right", expand=True, fill="x")
            self.entries[key] = entry

        # Membership Type Dropdown
        frame = tk.Frame(self)
        frame.pack(fill="x", padx=20, pady=5)
        tk.Label(frame, text="Tipo", width=15, anchor="w").pack(side="left")
        self.membership_type = ttk.Combobox(frame, values=['admin', 'atleta', 'sócio', 'atleta e sócio'])
        self.membership_type.set('atleta')
        self.membership_type.pack(side="right", expand=True, fill="x")

        # Submit Button
        tk.Button(self, text="Registar Sócio", bg="green", fg="white", command=self.save_user).pack(pady=20)

    def save_user(self):
        data = {k: v.get() for k, v in self.entries.items()}
        data['card_id'] = self.card_id
        data['membership_type'] = self.membership_type.get()

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (card_id, first_name, last_name, email, phone, nif, membership_type, monthly_fee)
                VALUES (:card_id, :first_name, :last_name, :email, :phone, :nif, :membership_type, :monthly_fee)
            ''', data)
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Sócio registado com sucesso!")
            self.destroy()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro", "NIF ou Email já existem no sistema.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
