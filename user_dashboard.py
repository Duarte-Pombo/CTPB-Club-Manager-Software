import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

DB_NAME = "CTPB.db"

# --- HELPER CLASSES ---

class TransactionDialog(tk.Toplevel):
    def __init__(self, parent, title, is_expense=False, default_amount=0.0):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x350")
        self.result = None
        self.is_expense = is_expense
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text="Categoria / Descrição:", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        if is_expense:
            self.cat_var = tk.StringVar()
            self.combo_cat = ttk.Combobox(self, textvariable=self.cat_var, state="readonly", width=30)
            self.combo_cat['values'] = ['Aluguer', 'Encordoamento (corda atleta)', 'Encordoamento (corda clube)', 'Overgrip', 'Bar', 'Outro']
            self.combo_cat.current(0)
            self.combo_cat.pack()
            self.entry_desc = tk.Entry(self, width=33)
            self.entry_desc.pack(pady=5)
            self.entry_desc.insert(0, "Detalhes opcionais...")
            self.entry_desc.bind("<FocusIn>", lambda e: self.entry_desc.delete(0, "end") if "Detalhes" in self.entry_desc.get() else None)
        else:
            self.entry_desc = tk.Entry(self, width=33)
            self.entry_desc.pack(pady=5)
            self.entry_desc.insert(0, title) 

        tk.Label(self, text="Valor (€):", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.amount_var = tk.DoubleVar(value=default_amount)
        self.entry_amount = tk.Entry(self, textvariable=self.amount_var, width=15, justify="center", font=("Arial", 12))
        self.entry_amount.pack()
        self.entry_amount.focus_set() 

        self.method_var = tk.StringVar(value="Numerário")
        if not is_expense:
            tk.Label(self, text="Método de Pagamento:", font=("Arial", 10, "bold")).pack(pady=(15, 5))
            self.combo_method = ttk.Combobox(self, textvariable=self.method_var, values=["Numerário", "Multibanco", "Transferência", "MB Way"], state="readonly", width=20)
            self.combo_method.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)
        self.bind('<Return>', lambda e: self.on_confirm())
        
        tk.Button(btn_frame, text="Confirmar", bg="#27ae60", fg="white", command=self.on_confirm).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancelar", bg="#c0392b", fg="white", command=self.destroy).pack(side="left", padx=10)
        self.wait_window(self)

    def on_confirm(self):
        try:
            val = float(self.entry_amount.get())
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")
            return
        
        desc = self.entry_desc.get()
        if self.is_expense and self.combo_cat.get() != "Outro":
            final_desc = f"{self.combo_cat.get()} - {desc}" if desc and "Detalhes" not in desc else self.combo_cat.get()
        else:
            final_desc = desc

        self.result = {"amount": val, "description": final_desc, "method": self.method_var.get() if not self.is_expense else None}
        self.destroy()

class QuotaActionDialog(tk.Toplevel):
    """Initial Action: Pay Full, Partial or Absent"""
    def __init__(self, parent, month_name):
        super().__init__(parent)
        self.title(f"Ação: {month_name}")
        self.geometry("400x200")
        self.action = None
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (200 // 2)
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text=f"Quota: {month_name}", font=("Arial", 12, "bold")).pack(pady=10)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(btn_frame, text="💰 Total", bg="#27ae60", fg="white", command=self.set_pay, height=2, width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="⚠️ Parcial", bg="#f1c40f", fg="black", command=self.set_partial, height=2, width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🚫 Ausente", bg="#7f8c8d", fg="white", command=self.set_absent, height=2, width=12).pack(side="left", padx=5)

        self.wait_window(self)

    def set_pay(self): self.action = "pay"; self.destroy()
    def set_partial(self): self.action = "partial"; self.destroy()
    def set_absent(self): self.action = "absent"; self.destroy()

class QuotaManageDialog(tk.Toplevel):
    """Management Action: Pay Rest or Cancel"""
    def __init__(self, parent, month_name, is_partial=False):
        super().__init__(parent)
        self.title(f"Gerir: {month_name}")
        self.geometry("350x180")
        self.action = None
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (350 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (180 // 2)
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text=f"Gerir Quota: {month_name}", font=("Arial", 12, "bold")).pack(pady=15)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10, fill="x", padx=10)

        if is_partial:
            tk.Button(btn_frame, text="💰 Liquidar Restante", bg="#2980b9", fg="white", command=self.set_pay_rest, height=2).pack(side="left", fill="x", expand=True, padx=5)

        tk.Button(btn_frame, text="🗑️ Anular / Devolver", bg="#c0392b", fg="white", command=self.set_cancel, height=2).pack(side="right", fill="x", expand=True, padx=5)

        self.wait_window(self)

    def set_pay_rest(self): self.action = "pay_rest"; self.destroy()
    def set_cancel(self): self.action = "cancel"; self.destroy()

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
        
        self.current_quota_year = tk.IntVar(value=datetime.now().year)

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

        tk.Label(sidebar, text="👤", bg="#2c3e50", fg="white", font=("Arial", 50)).pack(pady=(30, 10))
        tk.Label(sidebar, text=self.full_name, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"), wraplength=260).pack()
        tk.Label(sidebar, text=f"Cartão: {self.card_id}", bg="#2c3e50", fg="#bdc3c7").pack()
        self.lbl_balance = tk.Label(sidebar, text="0.00€", bg="#2c3e50", fg="white", font=("Arial", 24, "bold"))
        self.lbl_balance.pack(pady=30)

        btn_style = {"font": ("Arial", 11), "bd": 0, "pady": 8, "cursor": "hand2"}
        tk.Button(sidebar, text="➕ Nova Despesa (Dívida)", bg="#e74c3c", fg="white", width=25, **btn_style, command=self.add_expense).pack(pady=10)
        tk.Button(sidebar, text="💰 Registar Pagamento", bg="#27ae60", fg="white", width=25, **btn_style, command=self.add_generic_payment).pack(pady=10)

    def create_main_area(self):
        main_frame = tk.Frame(self, bg="#ecf0f1")
        main_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # Quota Header
        q_header = tk.Frame(main_frame, bg="#ecf0f1")
        q_header.pack(fill="x", pady=5)
        tk.Label(q_header, text="Estado das Quotas", font=("Arial", 12, "bold"), bg="#ecf0f1").pack(side="left")
        
        year_ctrl = tk.Frame(q_header, bg="#ecf0f1")
        year_ctrl.pack(side="right")
        tk.Button(year_ctrl, text="<", command=lambda: self.change_year(-1), width=3).pack(side="left")
        self.lbl_year = tk.Label(year_ctrl, textvariable=self.current_quota_year, font=("Arial", 12, "bold"), bg="white", width=6)
        self.lbl_year.pack(side="left", padx=5)
        tk.Button(year_ctrl, text=">", command=lambda: self.change_year(1), width=3).pack(side="left")

        self.grid_frame = tk.Frame(main_frame, bg="#ecf0f1")
        self.grid_frame.pack(fill="x", pady=5)

        split_frame = tk.Frame(main_frame, bg="#ecf0f1")
        split_frame.pack(fill="both", expand=True, pady=10)

        # Pending
        left_box = tk.LabelFrame(split_frame, text="⚠️ Dívidas Pendentes", bg="#ecf0f1", font=("Arial", 10, "bold"), fg="#c0392b")
        left_box.pack(side="left", fill="both", expand=True, padx=(0, 10))
        cols_pend = ("ID", "Data", "Desc", "Valor")
        self.tree_pending = ttk.Treeview(left_box, columns=cols_pend, show="headings")
        self.tree_pending.heading("ID", text="#"); self.tree_pending.column("ID", width=30)
        self.tree_pending.heading("Data", text="Data"); self.tree_pending.column("Data", width=80)
        self.tree_pending.heading("Desc", text="Descrição"); self.tree_pending.column("Desc", width=150)
        self.tree_pending.heading("Valor", text="Valor"); self.tree_pending.column("Valor", width=60, anchor="e")
        self.tree_pending.pack(fill="both", expand=True, pady=5)
        self.tree_pending.bind("<Double-1>", self.on_pending_double_click)
        tk.Label(left_box, text="* Duplo clique para liquidar (sem confirmação)", bg="#ecf0f1", fg="grey", font=("Arial", 8)).pack(anchor="w")

        # History
        right_box = tk.LabelFrame(split_frame, text="📜 Histórico de Pagamentos", bg="#ecf0f1", font=("Arial", 10, "bold"), fg="#27ae60")
        right_box.pack(side="right", fill="both", expand=True)
        cols_hist = ("Data", "Desc", "Valor", "Método")
        self.tree_history = ttk.Treeview(right_box, columns=cols_hist, show="headings")
        self.tree_history.heading("Data", text="Data"); self.tree_history.column("Data", width=90)
        self.tree_history.heading("Desc", text="Descrição"); self.tree_history.column("Desc", width=180)
        self.tree_history.heading("Valor", text="Valor"); self.tree_history.column("Valor", width=70, anchor="e")
        self.tree_history.heading("Método", text="Via"); self.tree_history.column("Método", width=80)
        self.tree_history.pack(fill="both", expand=True, pady=5)

    def change_year(self, delta):
        new_year = self.current_quota_year.get() + delta
        self.current_quota_year.set(new_year)
        self.refresh_quota_grid()

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
            cursor.execute("SELECT transaction_id, payment_date, notes, amount FROM transactions WHERE user_id = ? AND amount < 0 AND is_settled = 0 ORDER BY payment_date ASC", (self.user_id,))
            for row in cursor.fetchall(): self.tree_pending.insert("", "end", values=(row[0], row[1].split(" ")[0], row[2], f"{row[3]:.2f}€"))
            
            cursor.execute("SELECT payment_date, notes, amount, payment_method FROM transactions WHERE user_id = ? AND amount > 0 ORDER BY payment_date DESC LIMIT 50", (self.user_id,))
            for row in cursor.fetchall(): self.tree_history.insert("", "end", values=(row[0].split(" ")[0], row[1], f"+{row[2]:.2f}€", row[3]))

    def refresh_quota_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        
        months = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
        year = self.current_quota_year.get()

        status = {}
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT month, is_paid, amount_due FROM monthly_fees WHERE user_id=? AND year=?", (self.user_id, year))
            for r in cursor.fetchall(): status[r[0]] = {"paid": r[1], "amt": r[2]}

        self.create_q_btn(0, "Seguro", status.get(0), row=0, col=0, width=15)
        self.create_q_btn(13, "Quota Anual", status.get(13), row=0, col=1, width=15)

        m_frame = tk.Frame(self.grid_frame, bg="#ecf0f1")
        m_frame.grid(row=1, column=0, columnspan=12, pady=10)
        for i, m in enumerate(months):
            self.create_q_btn(i+1, m, status.get(i+1), parent=m_frame, row=0, col=i, width=5)

    def create_q_btn(self, mid, text, data, parent=None, row=0, col=0, width=10):
        if not parent: parent = self.grid_frame
        is_paid = data["paid"] if data else 0
        amount = data["amt"] if data else 0
        
        # COLOR LOGIC
        if is_paid == 1: color = "#3498db" if amount == 0 else "#27ae60"
        elif is_paid == 2: color = "#f1c40f"
        elif mid in range(1, 13) and self.monthly_fee_value <= 0: color = "#bdc3c7"
        else: color = "#c0392b"
        
        tk.Button(parent, text=text, bg=color, fg="white" if color != "#f1c40f" else "black", width=width,
                  command=lambda: self.on_quota_click(mid, text, is_paid, amount)).grid(row=row, column=col, padx=2)

    def on_quota_click(self, month_id, label, is_paid, current_amount_paid):
        selected_year = self.current_quota_year.get()

        # Define Full Amount Goal
        full_amt = 0.0
        if month_id == 0: full_amt = 15.0
        elif month_id == 13: full_amt = 40.0
        else: full_amt = self.monthly_fee_value

        # --- ALREADY PAID or PARTIAL ---
        if is_paid in [1, 2]: 
            # Open Management Dialog
            dlg = QuotaManageDialog(self, f"{label} {selected_year}", is_partial=(is_paid==2))
            
            if dlg.action == "cancel":
                # Logic: Refund Money, Delete Transaction, Reset Status
                self.cancel_quota_payment(month_id, selected_year, label, current_amount_paid)

            elif dlg.action == "pay_rest":
                # Logic: Calculate difference and pay
                remaining = max(0, full_amt - current_amount_paid)
                pay_dlg = TransactionDialog(self, f"Liquidar Restante: {label}", is_expense=False, default_amount=remaining)
                if pay_dlg.result:
                    new_val = pay_dlg.result['amount']
                    self.execute_transaction(new_val, f"Quota (Restante): {label} ({selected_year})", method=pay_dlg.result['method'])
                    
                    # Update DB: Add new amount to existing, set is_paid to 1 if fully paid (assuming they pay remainder)
                    total_paid = current_amount_paid + new_val
                    status = 1 if total_paid >= full_amt else 2
                    self.save_fee(month_id, selected_year, total_paid, status)
            return

        # --- UNPAID (RED) ---
        if month_id in range(1, 13) and self.monthly_fee_value <= 0: return

        choice_dlg = QuotaActionDialog(self, label)
        if not choice_dlg.action: return

        if choice_dlg.action == "absent":
            if messagebox.askyesno("Confirmar Ausência", f"Marcar '{label}' de {selected_year} como Ausente/Isento?"):
                self.save_fee(month_id, selected_year, 0, 1)

        elif choice_dlg.action == "pay":
            dlg = TransactionDialog(self, f"Pagar {label} {selected_year}", is_expense=False, default_amount=full_amt)
            if dlg.result:
                self.execute_transaction(dlg.result['amount'], f"Quota: {label} ({selected_year})", method=dlg.result['method'])
                self.save_fee(month_id, selected_year, dlg.result['amount'], 1)

        elif choice_dlg.action == "partial":
            dlg = TransactionDialog(self, f"Pagamento Parcial {label}", is_expense=False, default_amount=0.0)
            if dlg.result:
                self.execute_transaction(dlg.result['amount'], f"Parcial: {label} ({selected_year})", method=dlg.result['method'])
                self.save_fee(month_id, selected_year, dlg.result['amount'], 2)

    def cancel_quota_payment(self, month, year, label, amount_to_refund):
        """Deletes transaction records and updates balance"""
        if not messagebox.askyesno("Confirmar Anulação", f"Deseja anular o pagamento de {amount_to_refund}€?\nO movimento será apagado e o estado voltará a 'Não Pago'."):
            return

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Update User Balance (Remove the money that was added)
                cursor.execute("UPDATE users SET current_balance = current_balance - ? WHERE user_id = ?", (amount_to_refund, self.user_id))
                
                # 2. Delete Transaction(s)
                # We delete transactions that look like this quota payment for this user
                # We use LIKE to catch "Quota: Jan...", "Parcial: Jan...", "Quota (Restante): Jan..."
                pattern = f"%{label} ({year})%"
                cursor.execute("DELETE FROM transactions WHERE user_id=? AND amount > 0 AND notes LIKE ?", (self.user_id, pattern))
                
                # 3. Reset Monthly Fee
                cursor.execute("UPDATE monthly_fees SET is_paid=0, amount_due=0 WHERE user_id=? AND month=? AND year=?", (self.user_id, month, year))
                
                conn.commit()
            
            messagebox.showinfo("Sucesso", "Pagamento anulado com sucesso.")
            self.refresh_all()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao anular: {e}")

    def save_fee(self, month, year, amount, is_paid):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO monthly_fees (user_id, month, year, amount_due, is_paid, paid_date)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
                ON CONFLICT(user_id, month, year) DO UPDATE SET is_paid=?, amount_due=?
            """, (self.user_id, month, year, amount, is_paid, is_paid, amount))
        self.refresh_quota_grid()

    def add_expense(self):
        dlg = TransactionDialog(self, "Nova Despesa", is_expense=True)
        if dlg.result:
            self.execute_transaction(-abs(dlg.result['amount']), dlg.result['description'], method=None, is_settled=0)

    def add_generic_payment(self):
        dlg = TransactionDialog(self, "Registar Pagamento", is_expense=False)
        if dlg.result:
            self.execute_transaction(abs(dlg.result['amount']), dlg.result['description'], method=dlg.result['method'])

    def on_pending_double_click(self, event):
        item = self.tree_pending.selection()
        if not item: return
        vals = self.tree_pending.item(item, "values")
        
        amount_needed = abs(float(vals[3].replace("€","")))
        dlg = TransactionDialog(self, f"Liquidar: {vals[2]}", is_expense=False, default_amount=amount_needed)
        
        if dlg.result:
            self.execute_transaction(dlg.result['amount'], f"Pagamento: {vals[2]}", method=dlg.result['method'])
            with get_connection() as conn:
                conn.execute("UPDATE transactions SET is_settled=1 WHERE transaction_id=?", (vals[0],))
            self.refresh_tables()

    def execute_transaction(self, amount, note, method=None, is_settled=1):
        type_name = "pagamento" if amount > 0 else "despesa"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (user_id, type_id, amount, notes, payment_method, is_settled) VALUES (?, (SELECT type_id FROM payment_types WHERE type_name=?), ?, ?, ?, ?)", 
                           (self.user_id, type_name, amount, note, method, is_settled))
            cursor.execute("UPDATE users SET current_balance = current_balance + ? WHERE user_id = ?", (amount, self.user_id))
            conn.commit()
        self.refresh_all()