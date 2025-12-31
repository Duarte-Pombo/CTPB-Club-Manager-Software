import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog

DB_NAME = "CTPB.db"

def get_user_by_card(card_id):
    """Safely retrieves user data."""
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE card_id = ?", (card_id,))
        return cursor.fetchone()
    finally:
        conn.close()

class UserDashboard(tk.Toplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.user_id = user_data[0]
        self.card_id = user_data[1]
        self.title(f"Dashboard: {user_data[2]} {user_data[3]}")
        self.geometry("400x450")

        # Header Info
        tk.Label(self, text=f"{user_data[2]} {user_data[3]}", font=("Arial", 16, "bold")).pack(pady=10)

        self.balance_var = tk.DoubleVar(value=user_data[9])
        self.balance_label = tk.Label(self, text=f"Saldo: {self.balance_var.get():.2f}€",
                                      font=("Arial", 14), fg="green" if self.balance_var.get() >= 0 else "red")
        self.balance_label.pack(pady=5)

        tk.Label(self, text=f"Tipo: {user_data[7]} | NIF: {user_data[6]}", fg="gray").pack()

        # Action Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)

        tk.Button(btn_frame, text="📥 Registar Pagamento", bg="#27ae60", fg="white", width=20, height=2,
                  command=lambda: self.add_transaction("Pagamento", 1)).pack(pady=5)

        tk.Button(btn_frame, text="📤 Registar Despesa", bg="#e67e22", fg="white", width=20, height=2,
                  command=lambda: self.add_transaction("Despesa", -1)).pack(pady=5)

    def add_transaction(self, title, multiplier):
        amount = simpledialog.askfloat(title, f"Valor da {title} (€):", minvalue=0.01)
        if amount:
            final_amount = amount * multiplier
            self.process_transaction(final_amount, title)

    def process_transaction(self, amount, note):
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            # 1. Add Transaction Record
            cursor.execute("""
                INSERT INTO transactions (user_id, type_id, amount, notes)
                VALUES (?, (SELECT type_id FROM payment_types WHERE type_name = ? LIMIT 1), ?, ?)
            """, (self.user_id, note.lower(), amount, note))

            # 2. Update User Balance
            cursor.execute("UPDATE users SET current_balance = current_balance + ? WHERE user_id = ?",
                           (amount, self.user_id))

            conn.commit()

            # Update UI
            new_balance = self.balance_var.get() + amount
            self.balance_var.set(new_balance)
            self.balance_label.config(text=f"Saldo: {new_balance:.2f}€",
                                      fg="green" if new_balance >= 0 else "red")

            messagebox.showinfo("Sucesso", f"{note} de {abs(amount):.2f}€ registada.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na transação: {e}")
        finally:
            conn.close()

class UserRegistrationWindow(tk.Toplevel):
    def __init__(self, parent, card_id):
        super().__init__(parent)
        self.title("Registar Novo Sócio")
        self.geometry("450x600")
        self.card_id = card_id
        self.entries = {}

        # 1. Header
        tk.Label(self, text="Registo de Membro", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text=f"ID Cartão: {card_id}", fg="gray").pack()

        # 2. Form Container
        self.form_frame = tk.Frame(self)
        self.form_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Fields definition: (Label, DB_Key, is_mandatory)
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

        # 3. Membership Type (The Logic Trigger)
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

        # Monthly Fee field
        self.monthly_row = tk.Frame(self.quota_frame)
        tk.Label(self.monthly_row, text="Quota Mensal (€) *", width=15, anchor="w").pack(side="left")
        self.entry_monthly = tk.Entry(self.monthly_row)
        self.entry_monthly.pack(side="right", expand=True, fill="x")

        # Yearly Fee field (Note: We'll store this in the notes or a specific column if added later,
        # for now let's assume it's part of the user setup logic)
        self.yearly_row = tk.Frame(self.quota_frame)
        tk.Label(self.yearly_row, text="Quota Anual (€) *", width=15, anchor="w").pack(side="left")
        self.entry_yearly = tk.Entry(self.yearly_row)
        self.entry_yearly.insert(0, "40.00") # Default 40€
        self.entry_yearly.pack(side="right", expand=True, fill="x")

        # Initialize visibility
        self.toggle_quota_fields()

        # 5. Submit Button
        tk.Button(self, text="GRAVAR REGISTO", bg="#2ecc71", fg="white", font=("Arial", 11, "bold"),
                  command=self.save_user, height=2).pack(side="bottom", fill="x", padx=30, pady=20)

    def toggle_quota_fields(self, event=None):
        m_type = self.membership_type.get()

        # Hide everything first
        self.monthly_row.pack_forget()
        self.yearly_row.pack_forget()

        if m_type == 'atleta':
            self.monthly_row.pack(fill="x", pady=2)
        elif m_type == 'sócio':
            self.yearly_row.pack(fill="x", pady=2)
        elif m_type == 'atleta e sócio':
            self.monthly_row.pack(fill="x", pady=2)
            self.yearly_row.pack(fill="x", pady=2)
        # 'admin' shows no quota fields

    def save_user(self):
        # Gather basic data
        data = {k: v.get().strip() for k, v in self.entries.items()}
        data['card_id'] = self.card_id
        data['membership_type'] = self.membership_type.get()

        # Determine monthly fee based on type
        m_type = data['membership_type']
        if m_type in ['atleta', 'atleta e sócio']:
            data['monthly_fee'] = self.entry_monthly.get().strip()
        else:
            data['monthly_fee'] = 0.0

        # 1. Validation Logic
        if not data['first_name'] or not data['last_name']:
            messagebox.showwarning("Aviso", "Nome e Apelido são obrigatórios!")
            return

        if m_type in ['atleta', 'atleta e sócio'] and not data['monthly_fee']:
            messagebox.showwarning("Aviso", "Defina o valor da quota mensal para atletas!")
            return

        # 2. Database Execution
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (card_id, first_name, last_name, email, phone, nif, membership_type, monthly_fee)
                VALUES (:card_id, :first_name, :last_name, :email, :phone, :nif, :membership_type, :monthly_fee)
            ''', data)
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", f"Membro {data['first_name']} registado com sucesso!")
            self.destroy()

        except sqlite3.IntegrityError:
            messagebox.showerror("Erro de Duplicação", "Este NIF, Email ou Cartão já existe no sistema.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível gravar: {e}")
