import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import user_dashboard
from datetime import datetime

DB_NAME = "CTPB.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10)

class MainDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CTPB - Gestão do Clube")
        self.geometry("1100x700")
        self.configure(bg="#ecf0f1")

        # Define Styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.create_toolbar()
        self.create_user_list()
        self.create_action_bar()
        self.refresh_users()

    def create_toolbar(self):
        tool_frame = tk.Frame(self, bg="white", pady=10, padx=10)
        tool_frame.pack(fill="x", side="top")

        tk.Label(tool_frame, text="🔍 Pesquisar:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        
        # --- FIX: Use trace_add instead of trace for Python 3.14+ ---
        self.search_var.trace_add("write", lambda *args: self.refresh_users()) 
        
        entry_search = tk.Entry(tool_frame, textvariable=self.search_var, width=30, font=("Arial", 11))
        entry_search.pack(side="left", padx=5)
        tk.Label(tool_frame, text="(Nome, ID ou NIF)", bg="white", fg="grey", font=("Arial", 9)).pack(side="left", padx=(0, 20))

        tk.Label(tool_frame, text="📅 Época:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.year_var = tk.IntVar(value=datetime.now().year)
        tk.Spinbox(tool_frame, from_=2020, to=2030, textvariable=self.year_var, width=5, command=self.refresh_users).pack(side="left", padx=5)

        self.filter_debt_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tool_frame, text="Com Dívidas Ativas", variable=self.filter_debt_var, bg="white", command=self.refresh_users).pack(side="left", padx=10)

        self.filter_quota_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tool_frame, text="Quotas em Atraso", variable=self.filter_quota_var, bg="white", command=self.refresh_users).pack(side="left", padx=10)

    def create_user_list(self):
        list_frame = tk.Frame(self, bg="#ecf0f1", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side="right", fill="y")

        columns = ("uid", "name", "nif", "email", "type", "phone", "action")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", yscrollcommand=scroll.set)
        
        headers = [("uid", "ID", 50), ("name", "Nome Completo", 250), ("nif", "NIF", 100), 
                   ("email", "Email", 200), ("type", "Tipo", 100), ("phone", "Telemóvel", 100), ("action", "Eliminar", 60)]
        
        for col, text, width in headers:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center" if col != "name" and col != "email" else "w")

        self.tree.pack(fill="both", expand=True)
        scroll.config(command=self.tree.yview)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<ButtonRelease-1>", self.on_single_click) 
        self.tree.tag_configure("has_debt", foreground="#c0392b")

    def create_action_bar(self):
        bar_frame = tk.Frame(self, bg="#2c3e50", height=60)
        bar_frame.pack(side="bottom", fill="x")
        bar_frame.pack_propagate(False)

        btn_style = {"bg": "#34495e", "fg": "white", "font": ("Arial", 10, "bold"), "bd": 0, "padx": 15, "pady": 10}
        tk.Button(bar_frame, text="📄 Relatório Mensal", command=self.not_implemented, **btn_style).pack(side="left", padx=10, pady=10)
        tk.Button(bar_frame, text="📊 Relatório Anual", command=self.not_implemented, **btn_style).pack(side="left", padx=10, pady=10)
        tk.Button(bar_frame, text="🔒 Cópia Segurança", command=self.not_implemented, **btn_style).pack(side="right", padx=10, pady=10)
        tk.Button(bar_frame, text="🗑️ Reset Database", bg="#c0392b", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=10, command=self.not_implemented).pack(side="right", padx=10, pady=10)

    def refresh_users(self):
        for item in self.tree.get_children(): self.tree.delete(item)

        search_term = self.search_var.get().strip().lower()
        target_year = self.year_var.get()
        
        # Soft Delete Check: only show active users
        query = "SELECT user_id, first_name, last_name, nif, email, membership_type, phone, current_balance, monthly_fee FROM users WHERE is_active = 1"
        params = []

        if search_term:
            query += " AND (lower(first_name || ' ' || last_name) LIKE ? OR CAST(user_id AS TEXT) LIKE ? OR nif LIKE ?)"
            term_wild = f"%{search_term}%"
            params.extend([term_wild, term_wild, term_wild])

        if self.filter_debt_var.get():
            query += " AND current_balance < 0"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                uid, fname, lname, nif, email, mtype, phone, balance, mfee = row
                
                if self.filter_quota_var.get():
                    if mfee <= 0: continue 
                    cursor.execute("SELECT count(*) FROM monthly_fees WHERE user_id=? AND year=? AND is_paid=1", (uid, target_year))
                    if cursor.fetchone()[0] >= 12: continue

                full_name = f"{fname} {lname}"
                debt_tag = "has_debt" if balance < 0 else ""
                self.tree.insert("", "end", values=(uid, full_name, nif, email, mtype, phone, "❌"), tags=(debt_tag,))

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        user_id = self.tree.item(item, "values")[0]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()

        if user_data:
            user_dashboard.UserDashboard(self, user_data)
            self.wait_window(self.children.get(self.focus_get())) 
            self.refresh_users()

    def on_single_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) == "#7":
            item = self.tree.identify_row(event.y)
            vals = self.tree.item(item, "values")
            if vals: self.soft_delete_user(vals[0], vals[1])

    def soft_delete_user(self, uid, name):
        if messagebox.askyesno("Confirmar", f"Deseja remover o sócio (Soft Delete):\n{name}?"):
            try:
                with get_connection() as conn:
                    conn.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (uid,))
                self.refresh_users()
                messagebox.showinfo("Sucesso", "Utilizador desativado.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao desativar: {e}")

    def not_implemented(self):
        messagebox.showinfo("Em construção", "Esta funcionalidade será implementada no próximo passo.")