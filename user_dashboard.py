import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

DB_NAME = "CTPB.db"

# --- HELPER CLASSES FOR DIALOGS ---

class TransactionDialog(tk.Toplevel):
    """Generic dialog for Payments or Expenses"""
    def __init__(self, parent, title, is_expense=False, default_amount=0.0):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x350")
        self.result = None
        self.is_expense = is_expense

        self.transient(parent)
        self.grab_set()

        # 1. Category / Description
        tk.Label(self, text="Categoria / Descrição:", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        if is_expense:
            self.cat_var = tk.StringVar()
            self.combo_cat = ttk.Combobox(self, textvariable=self.cat_var, state="readonly", width=30)
            self.combo_cat['values'] = [
                'Aluguer',
                'Encordoamento (corda atleta)',
                'Encordoamento (corda clube)',
                'Overgrip',
                'Bar',
                'Outro'
            ]
            self.combo_cat.current(0)
            self.combo_cat.pack()
            self.combo_cat.bind("<<ComboboxSelected>>", self.toggle_other)

            self.entry_desc = tk.Entry(self, width=33)
            self.entry_desc.pack(pady=5)
            self.entry_desc.insert(0, "Detalhes opcionais...")
            self.entry_desc.config(fg="grey")
            self.entry_desc.bind("<FocusIn>", lambda e: self.entry_desc.delete(0, "end") if "Detalhes" in self.entry_desc.get() else None)
        else:
            self.entry_desc = tk.Entry(self, width=33)
            self.entry_desc.pack(pady=5)
            self.entry_desc.insert(0, title) 

        # 2. Amount
        tk.Label(self, text="Valor (€):", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.amount_var = tk.DoubleVar(value=default_amount)
        self.entry_amount = tk.Entry(self, textvariable=self.amount_var, width=15, justify="center", font=("Arial", 12))
        self.entry_amount.pack()

        # 3. Payment Method (Only for Payments)
        self.method_var = tk.StringVar(value="Numerário")
        if not is_expense:
            tk.Label(self, text="Método de Pagamento:", font=("Arial", 10, "bold")).pack(pady=(15, 5))
            methods = ["Numerário", "Multibanco", "Transferência", "MB Way"]
            self.combo_method = ttk.Combobox(self, textvariable=self.method_var, values=methods, state="readonly", width=20)
            self.combo_method.pack()

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)
        tk.Button(btn_frame, text="Confirmar", bg="#27ae60", fg="white", command=self.on_confirm).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancelar", bg="#c0392b", fg="white", command=self.destroy).pack(side="left", padx=10)

        self.wait_window(self)

    def toggle_other(self, event):
        if self.combo_cat.get() == "Outro":
            self.entry_desc.delete(0, "end")
            self.entry_desc.focus_set()

    def on_confirm(self):
        try:
            val = float(self.entry_amount.get())
            if val < 0: raise ValueError # Allow 0 for corrections, but usually positive input here
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")
            return

        desc = self.entry_desc.get()
        if self.is_expense:
            cat = self.combo_cat.get()
            if cat != "Outro":
                final_desc = f"{cat} - {desc}" if desc and "Detalhes" not in desc else cat
            else:
                final_desc = desc
        else:
            final_desc = desc

        self.result = {
            "amount": val,
            "description": final_desc,
            "method": self.method_var.get() if not self.is_expense else None
        }
        self.destroy()

class QuotaActionDialog(tk.Toplevel):
    """Specific dialog to choose between Paying or Marking as Absent"""
    def __init__(self, parent, month_name):
        super().__init__(parent)
        self.title(f"Ação: {month_name}")
        self.geometry("350x180")
        self.action = None
        
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=f"Quota: {month_name}", font=("Arial", 12, "bold")).pack(pady=15)
        tk.Label(self, text="Selecione uma ação:", fg="grey").pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20, fill="x", padx=20)

        # Button: PAY
        tk.Button(btn_frame, text="💰 Pagar Quota", bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  command=self.set_pay, height=2).pack(side="left", fill="x", expand=True, padx=5)

        # Button: ABSENT
        tk.Button(btn_frame, text="🚫 Marcar Ausente", bg="#7f8c8d", fg="white", font=("Arial", 10),
                  command=self.set_absent, height=2).pack(side="right", fill="x", expand=True, padx=5)

        self.wait_window(self)

    def set_pay(self):
        self.action = "pay"
        self.destroy()

    def set_absent(self):
        self.action = "absent"
        self.destroy()


# --- MAIN DASHBOARD ---

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10)

class UserDashboard(tk.Toplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.user_id = user_data[0]
        self.card_id = user_data[1]
        self.full_name = f"{user_data[2]} {user_data[3]}"
        self.membership_type = user_data[7]
        self.monthly_fee_value = user_data[8]

        self.title(f"Painel de Sócio: {self.full_name}")
        self.geometry("1200x700")
        self.configure(bg="#ecf0f1")

        self.create_sidebar()
        self.create_main_area()
        self.refresh_all()

    def create_sidebar(self):
        sidebar = tk.Frame(self, bg="#2c3e50", width=280)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Profile
        tk.Label(sidebar, text="👤", bg="#2c3e50", fg="white", font=("Arial", 50)).pack(pady=(30, 10))
        tk.Label(sidebar, text=self.full_name, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"), wraplength=260).pack()
        tk.Label(sidebar, text=f"Cartão: {self.card_id}", bg="#2c3e50", fg="#bdc3c7").pack()

        self.lbl_balance = tk.Label(sidebar, text="0.00€", bg="#2c3e50", fg="white", font=("Arial", 24, "bold"))
        self.lbl_balance.pack(pady=30)

        # Buttons
        btn_style = {"font": ("Arial", 11), "bd": 0, "pady": 8, "cursor": "hand2"}
        tk.Button(sidebar, text="➕ Nova Despesa (Dívida)", bg="#e74c3c", fg="white", width=25, **btn_style,
                  command=self.add_expense).pack(pady=10)

        tk.Button(sidebar, text="💰 Registar Pagamento", bg="#27ae60", fg="white", width=25, **btn_style,
                  command=self.add_generic_payment).pack(pady=10)

    def create_main_area(self):
        main_frame = tk.Frame(self, bg="#ecf0f1")
        main_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # 1. QUOTA GRID
        tk.Label(main_frame, text="Estado das Quotas", font=("Arial", 12, "bold"), bg="#ecf0f1").pack(anchor="w")
        self.grid_frame = tk.Frame(main_frame, bg="#ecf0f1")
        self.grid_frame.pack(fill="x", pady=5)

        # 2. SPLIT TABLES (Left: Pending, Right: History)
        split_frame = tk.Frame(main_frame, bg="#ecf0f1")
        split_frame.pack(fill="both", expand=True, pady=10)

        # --- LEFT: PENDING EXPENSES ---
        left_box = tk.LabelFrame(split_frame, text="⚠️ Dívidas Pendentes", bg="#ecf0f1", font=("Arial", 10, "bold"), fg="#c0392b")
        left_box.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cols_pend = ("ID", "Data", "Desc", "Valor")
        self.tree_pending = ttk.Treeview(left_box, columns=cols_pend, show="headings")
        self.tree_pending.heading("ID", text="#")
        self.tree_pending.column("ID", width=30)
        self.tree_pending.heading("Data", text="Data")
        self.tree_pending.column("Data", width=80)
        self.tree_pending.heading("Desc", text="Descrição")
        self.tree_pending.column("Desc", width=150)
        self.tree_pending.heading("Valor", text="Valor")
        self.tree_pending.column("Valor", width=60, anchor="e")
        self.tree_pending.pack(fill="both", expand=True, pady=5)

        self.tree_pending.bind("<Double-1>", self.on_pending_double_click)
        tk.Label(left_box, text="* Duplo clique para liquidar", bg="#ecf0f1", fg="grey", font=("Arial", 8)).pack(anchor="w")

        # --- RIGHT: HISTORY ---
        right_box = tk.LabelFrame(split_frame, text="📜 Histórico de Pagamentos", bg="#ecf0f1", font=("Arial", 10, "bold"), fg="#27ae60")
        right_box.pack(side="right", fill="both", expand=True)

        cols_hist = ("Data", "Desc", "Valor", "Método")
        self.tree_history = ttk.Treeview(right_box, columns=cols_hist, show="headings")
        self.tree_history.heading("Data", text="Data")
        self.tree_history.column("Data", width=90)
        self.tree_history.heading("Desc", text="Descrição")
        self.tree_history.column("Desc", width=180)
        self.tree_history.heading("Valor", text="Valor")
        self.tree_history.column("Valor", width=70, anchor="e")
        self.tree_history.heading("Método", text="Via")
        self.tree_history.column("Método", width=80)
        self.tree_history.pack(fill="both", expand=True, pady=5)

    def refresh_all(self):
        self.refresh_balance()
        self.refresh_quota_grid()
        self.refresh_tables()

    def refresh_balance(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_balance FROM users WHERE user_id = ?", (self.user_id,))
            bal = cursor.fetchone()[0]
            self.lbl_balance.config(text=f"{bal:.2f}€", fg="#2ecc71" if bal >= 0 else "#e74c3c")

    def refresh_tables(self):
        for i in self.tree_pending.get_children(): self.tree_pending.delete(i)
        for i in self.tree_history.get_children(): self.tree_history.delete(i)

        with get_connection() as conn:
            cursor = conn.cursor()

            # PENDING
            cursor.execute("""
                SELECT transaction_id, payment_date, notes, amount
                FROM transactions
                WHERE user_id = ? AND amount < 0 AND is_settled = 0
                ORDER BY payment_date ASC
            """, (self.user_id,))
            for row in cursor.fetchall():
                d_str = row[1].split(" ")[0]
                self.tree_pending.insert("", "end", values=(row[0], d_str, row[2], f"{row[3]:.2f}€"))

            # HISTORY
            cursor.execute("""
                SELECT payment_date, notes, amount, payment_method
                FROM transactions
                WHERE user_id = ? AND amount > 0
                ORDER BY payment_date DESC LIMIT 50
            """, (self.user_id,))
            for row in cursor.fetchall():
                d_str = row[0].split(" ")[0]
                self.tree_history.insert("", "end", values=(d_str, row[1], f"+{row[2]:.2f}€", row[3]))

    def refresh_quota_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()

        months = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
        year = datetime.now().year

        # Fetch Status (is_paid, amount_due)
        status = {}
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT month, is_paid, amount_due FROM monthly_fees WHERE user_id=? AND year=?", (self.user_id, year))
            for r in cursor.fetchall(): 
                status[r[0]] = {"paid": r[1], "amt": r[2]}

        # Insurance & Annual
        self.create_q_btn(0, "Seguro", status.get(0), row=0, col=0, width=15)
        self.create_q_btn(13, "Quota Anual", status.get(13), row=0, col=1, width=15)

        # Months
        m_frame = tk.Frame(self.grid_frame, bg="#ecf0f1")
        m_frame.grid(row=1, column=0, columnspan=12, pady=10)
        for i, m in enumerate(months):
            self.create_q_btn(i+1, m, status.get(i+1), parent=m_frame, row=0, col=i, width=5)

    def create_q_btn(self, mid, text, data, parent=None, row=0, col=0, width=10):
        if not parent: parent = self.grid_frame
        
        is_paid = data["paid"] if data else 0
        amount = data["amt"] if data else 0

        # --- COLOR LOGIC ---
        if is_paid:
            if amount == 0:
                color = "#3498db" # BLUE = Absent / Free
            else:
                color = "#27ae60" # GREEN = Paid
        elif mid in range(1, 13) and self.monthly_fee_value <= 0:
            color = "#bdc3c7" # GREY = Disabled/Not applicable
        else:
            color = "#c0392b" # RED = Unpaid

        tk.Button(parent, text=text, bg=color, fg="white", width=width,
                  command=lambda: self.on_quota_click(mid, text, is_paid)).grid(row=row, column=col, padx=2)

    def on_quota_click(self, month_id, label, is_paid):
        if is_paid: return
        if month_id in range(1, 13) and self.monthly_fee_value <= 0: return

        # Default amount logic
        def_amt = 0.0
        if month_id == 0: def_amt = 15.0 # Insurance
        elif month_id == 13: def_amt = 40.0 # Annual
        else: def_amt = self.monthly_fee_value

        # --- STEP 1: Ask Action (Pay vs Absent) ---
        choice_dlg = QuotaActionDialog(self, label)
        if not choice_dlg.action: return

        # --- STEP 2: Process Action ---
        if choice_dlg.action == "absent":
            if messagebox.askyesno("Confirmar Ausência", f"Marcar '{label}' como Ausente/Isento?\n(O valor a pagar será 0.00€)"):
                # Insert as Paid but with 0 amount
                with get_connection() as conn:
                    conn.execute("""
                        INSERT INTO monthly_fees (user_id, month, year, amount_due, is_paid, paid_date)
                        VALUES (?, ?, ?, 0, 1, DATE('now'))
                        ON CONFLICT(user_id, month, year) DO UPDATE SET is_paid=1, amount_due=0
                    """, (self.user_id, month_id, datetime.now().year))
                self.refresh_quota_grid()

        elif choice_dlg.action == "pay":
            # Proceed to Payment Dialog
            dlg = TransactionDialog(self, f"Pagar {label}", is_expense=False, default_amount=def_amt)
            if dlg.result:
                # 1. Register transaction
                self.execute_transaction(dlg.result['amount'], f"Quota: {label}", method=dlg.result['method'])
                # 2. Update monthly_fees table
                with get_connection() as conn:
                    conn.execute("""
                        INSERT INTO monthly_fees (user_id, month, year, amount_due, is_paid, paid_date)
                        VALUES (?, ?, ?, ?, 1, DATE('now'))
                        ON CONFLICT(user_id, month, year) DO UPDATE SET is_paid=1, amount_due=?
                    """, (self.user_id, month_id, datetime.now().year, dlg.result['amount'], dlg.result['amount']))
                self.refresh_quota_grid()

    # --- ACTIONS ---

    def add_expense(self):
        dlg = TransactionDialog(self, "Nova Despesa", is_expense=True)
        if dlg.result:
            amt = -abs(dlg.result['amount'])
            note = dlg.result['description']
            self.execute_transaction(amt, note, method=None, is_settled=0)

    def add_generic_payment(self):
        dlg = TransactionDialog(self, "Registar Pagamento", is_expense=False)
        if dlg.result:
            self.execute_transaction(abs(dlg.result['amount']), dlg.result['description'], method=dlg.result['method'])

    def on_pending_double_click(self, event):
        item = self.tree_pending.selection()
        if not item: return
        vals = self.tree_pending.item(item, "values")
        t_id = vals[0]
        desc = vals[2]
        amount_needed = abs(float(vals[3].replace("€", "")))

        if messagebox.askyesno("Liquidar", f"Deseja liquidar a dívida:\n'{desc}' ({amount_needed}€)?"):
            dlg = TransactionDialog(self, f"Liquidar: {desc}", is_expense=False, default_amount=amount_needed)
            if dlg.result:
                self.execute_transaction(dlg.result['amount'], f"Pagamento: {desc}", method=dlg.result['method'])
                with get_connection() as conn:
                    conn.execute("UPDATE transactions SET is_settled=1 WHERE transaction_id=?", (t_id,))
                self.refresh_tables()

    def execute_transaction(self, amount, note, method=None, is_settled=1):
        type_name = "pagamento" if amount > 0 else "despesa"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, type_id, amount, notes, payment_method, is_settled)
                VALUES (?, (SELECT type_id FROM payment_types WHERE type_name=?), ?, ?, ?, ?)
            """, (self.user_id, type_name, amount, note, method, is_settled))

            cursor.execute("UPDATE users SET current_balance = current_balance + ? WHERE user_id = ?", (amount, self.user_id))
            conn.commit()
        self.refresh_all()