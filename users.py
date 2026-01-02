import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog

DB_NAME = "CTPB.db"

def get_connection():
    """Returns a connection with a timeout to prevent 'database locked' errors."""
    return sqlite3.connect(DB_NAME, timeout=10)

def get_user_by_card(card_id):
    """Safely retrieves user data using a context manager."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE card_id = ?", (card_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error in get_user_by_card: {e}")
        return None

class UserRegistrationWindow(tk.Toplevel):
    def __init__(self, parent, card_id):
        super().__init__(parent)
        self.title("Registar Novo Sócio")
        self.geometry("450x650")
        self.card_id = card_id
        self.entries = {}

        # 1. Header
        tk.Label(self, text="Registo de Membro", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text=f"ID Cartão: {card_id}", fg="gray").pack()

        # 2. Form Container
        self.form_frame = tk.Frame(self)
        self.form_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Fields definition
        self.field_definitions = [
            ("Nome *", "first_name", True),
            ("Apelido *", "last_name", True),
            ("Email", "email", False),
            ("Telemóvel", "phone", False),
            ("NIF", "nif", False),
        ]

        for label_text, key, mandatory in self.field_definitions:
            row = tk.Frame(self.form_frame)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, width=15, anchor="w").pack(side="left")
            entry = tk.Entry(row)
            entry.pack(side="right", expand=True, fill="x")
            self.entries[key] = entry

        # 3. Membership Type
        row = tk.Frame(self.form_frame)
        row.pack(fill="x", pady=10)
        tk.Label(row, text="Tipo de Sócio *", width=15, anchor="w", font=("Arial", 10, "bold")).pack(side="left")
        self.membership_type = ttk.Combobox(row, values=['admin', 'atleta', 'sócio', 'atleta e sócio'], state="readonly")
        self.membership_type.set('atleta')
        self.membership_type.pack(side="right", expand=True, fill="x")
        self.membership_type.bind("<<ComboboxSelected>>", self.toggle_quota_fields)

        # 4. Conditional Quota Fields
        self.quota_frame = tk.LabelFrame(self.form_frame, text="Configuração de Quotas", padx=10, pady=10)
        self.quota_frame.pack(fill="x", pady=10)

        self.monthly_row = tk.Frame(self.quota_frame)
        tk.Label(self.monthly_row, text="Quota Mensal (€) *", width=15, anchor="w").pack(side="left")
        self.entry_monthly = tk.Entry(self.monthly_row)
        self.entry_monthly.pack(side="right", expand=True, fill="x")

        self.yearly_row = tk.Frame(self.quota_frame)
        tk.Label(self.yearly_row, text="Quota Anual (€) *", width=15, anchor="w").pack(side="left")
        self.entry_yearly = tk.Entry(self.yearly_row)
        self.entry_yearly.insert(0, "40.00")
        self.yearly_row.pack(fill="x", pady=2) # Default visible for athletes/socios

        self.toggle_quota_fields()

        # 5. Submit Button
        tk.Button(self, text="GRAVAR REGISTO", bg="#2ecc71", fg="white", font=("Arial", 11, "bold"),
                  command=self.save_user, height=2).pack(side="bottom", fill="x", padx=30, pady=20)

    def toggle_quota_fields(self, event=None):
        m_type = self.membership_type.get()
        self.monthly_row.pack_forget()
        self.yearly_row.pack_forget()

        if m_type == 'atleta':
            self.monthly_row.pack(fill="x", pady=2)
        elif m_type == 'sócio':
            self.yearly_row.pack(fill="x", pady=2)
        elif m_type == 'atleta e sócio':
            self.monthly_row.pack(fill="x", pady=2)
            self.yearly_row.pack(fill="x", pady=2)

    def save_user(self):
        # 1. Gather and Clean Data
        data = {k: v.get().strip() for k, v in self.entries.items()}
        data['card_id'] = self.card_id
        data['membership_type'] = self.membership_type.get()

        # Mandatory Field Check
        if not data['first_name'] or not data['last_name']:
            messagebox.showwarning("Aviso", "Nome e Apelido são obrigatórios!")
            return

        # NIF Logic: Use 999999990 if empty
        user_nif = data.get('nif') or "999999990"
        data['nif'] = user_nif

        # Monthly Fee Logic
        m_type = data['membership_type']
        if m_type in ['atleta', 'atleta e sócio']:
            data['monthly_fee'] = self.entry_monthly.get().strip() or 0.0
        else:
            data['monthly_fee'] = 0.0

        # 2. Database Execution
        try:
            with get_connection() as conn: # Use helper with timeout
                cursor = conn.cursor()

                # Check uniqueness ONLY if NIF is not the generic one
                if user_nif != "999999990":
                    cursor.execute("SELECT user_id FROM users WHERE nif = ?", (user_nif,))
                    if cursor.fetchone():
                        messagebox.showerror("Erro", f"O NIF {user_nif} já está registado noutro sócio.")
                        return

                # Execute Insert
                cursor.execute('''
                    INSERT INTO users (card_id, first_name, last_name, email, phone, nif, membership_type, monthly_fee)
                    VALUES (:card_id, :first_name, :last_name, :email, :phone, :nif, :membership_type, :monthly_fee)
                ''', data)

            # 3. Finalize
            messagebox.showinfo("Sucesso", f"Membro {data['first_name']} registado!")
            self.destroy()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro", "O Email ou ID do Cartão já existe no sistema.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao gravar: {e}")
