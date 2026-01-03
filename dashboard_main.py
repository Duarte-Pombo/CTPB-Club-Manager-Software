import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
import sqlite3
import user_dashboard
from datetime import datetime
import os

DB_NAME = "CTPB.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10)

class MonthSelectorDialog(tk.Toplevel):
    """Dialog to checkmark specific overdue months"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Selecionar Meses em Atraso")
        self.geometry("320x650") # Increased height to fit all months + button
        self.selected_months = []
        self.transient(parent)
        self.grab_set()

        # --- 1. BUTTON AREA (Packed at Bottom) ---
        # We pack this first using side="bottom" so it never gets pushed off screen
        btn_frame = tk.Frame(self, pady=15, bg="#ecf0f1")
        btn_frame.pack(side="bottom", fill="x")
        
        tk.Button(btn_frame, text="✅ APLICAR FILTRO", bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                  command=self.apply, height=2).pack(fill="x", padx=20)

        # --- 2. SCROLLABLE CONTENT AREA ---
        # Creating a canvas to ensure it fits on smaller screens if needed
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # --- 3. CHECKBOXES ---
        tk.Label(scrollable_frame, text="Verificar falta de pagamento em:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

        self.vars = {}
        
        # Extras (Insurance/Annual)
        self.extras = [("Seguro", 0), ("Quota Anual", 13)]
        for name, code in self.extras:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(scrollable_frame, text=name, variable=var, anchor="w", font=("Arial", 11))
            chk.pack(fill="x", pady=2)
            self.vars[code] = var
            
        tk.Frame(scrollable_frame, height=2, bg="#bdc3c7").pack(fill="x", pady=10)

        # Months
        months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        for i, m in enumerate(months):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(scrollable_frame, text=m, variable=var, anchor="w", font=("Arial", 11))
            chk.pack(fill="x", pady=2)
            self.vars[i+1] = var

    def apply(self):
        self.selected_months = [code for code, var in self.vars.items() if var.get()]
        self.destroy()

class MainDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CTPB - Gestão do Clube")
        self.geometry("1150x700")
        self.configure(bg="#ecf0f1")

        # Define Styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        # State variables for filters
        self.filter_months_list = [] # List of integers (0-13)

        self.create_toolbar()
        self.create_user_list()
        self.create_action_bar()
        self.refresh_users()

    def create_toolbar(self):
        tool_frame = tk.Frame(self, bg="white", pady=10, padx=10)
        tool_frame.pack(fill="x", side="top")

        # SEARCH
        tk.Label(tool_frame, text="🔍 Pesquisar:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_users()) 
        tk.Entry(tool_frame, textvariable=self.search_var, width=20, font=("Arial", 11)).pack(side="left", padx=5)

        # SEASON (ÉPOCA)
        tk.Label(tool_frame, text="📅 Época:", bg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(15, 5))
        self.year_var = tk.IntVar(value=datetime.now().year)
        tk.Spinbox(tool_frame, from_=2020, to=2030, textvariable=self.year_var, width=5, command=self.refresh_users).pack(side="left", padx=5)

        # DEBT FILTER (Pending Transactions)
        self.filter_debt_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tool_frame, text="Com Dívidas (Despesas)", variable=self.filter_debt_var, bg="white", command=self.refresh_users).pack(side="left", padx=15)

        # QUOTA FILTER BUTTON
        self.btn_quota_filter = tk.Button(tool_frame, text="Filtro Quotas (Todos)", bg="#ecf0f1", command=self.open_month_selector)
        self.btn_quota_filter.pack(side="left", padx=10)
        
        # EXPORT BUTTON
        tk.Button(tool_frame, text="🖨️ Imprimir Lista", bg="#95a5a6", fg="white", command=self.export_list).pack(side="right", padx=10)

    def open_month_selector(self):
        dlg = MonthSelectorDialog(self)
        self.wait_window(dlg)
        self.filter_months_list = dlg.selected_months
        
        # Update Button Text
        if not self.filter_months_list:
            self.btn_quota_filter.config(text="Filtro Quotas (Todos)", bg="#ecf0f1", fg="black")
        else:
            self.btn_quota_filter.config(text=f"Filtro: {len(self.filter_months_list)} Meses Sel.", bg="#e67e22", fg="white")
        
        self.refresh_users()

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
        
        tk.Button(bar_frame, text="📄 Relatório Mensal", command=self.generate_monthly_report, **btn_style).pack(side="left", padx=10, pady=10)
        tk.Button(bar_frame, text="📊 Relatório Anual", command=self.generate_yearly_report, **btn_style).pack(side="left", padx=10, pady=10)
        
        tk.Button(bar_frame, text="🔒 Cópia Segurança", command=self.backup_database, **btn_style).pack(side="right", padx=10, pady=10)
        tk.Button(bar_frame, text="📂 Restaurar Cópia", command=self.restore_database, **btn_style).pack(side="right", padx=10, pady=10)
        tk.Button(bar_frame, text="🗑️ Reset Database", bg="#c0392b", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=10, command=self.reset_database).pack(side="right", padx=10, pady=10)

    # --- MAIN FILTER LOGIC ---

    def refresh_users(self):
        # 1. Clear List
        for item in self.tree.get_children(): self.tree.delete(item)

        search_term = self.search_var.get().strip().lower()
        target_year = self.year_var.get()
        
        # 2. Base Query
        query = "SELECT user_id, first_name, last_name, nif, email, membership_type, phone, current_balance, monthly_fee FROM users WHERE is_active = 1"
        params = []

        # 3. Apply Search
        if search_term:
            query += " AND (lower(first_name || ' ' || last_name) LIKE ? OR CAST(user_id AS TEXT) LIKE ? OR nif LIKE ?)"
            term_wild = f"%{search_term}%"
            params.extend([term_wild, term_wild, term_wild])

        # 4. Apply Debt Filter (Specific Unsettled Transactions)
        # We use a subquery to find users who have unsettled expense transactions
        if self.filter_debt_var.get():
            query += " AND user_id IN (SELECT user_id FROM transactions WHERE is_settled = 0 AND amount < 0)"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                uid, fname, lname, nif, email, mtype, phone, balance, mfee = row
                
                # 5. Apply Quota Filter (Python side)
                # If specific months are selected, we must check if the user has PAID them for the target year.
                # If the user is missing a payment for ANY of the selected months, we show them.
                if self.filter_months_list:
                    # If user has no monthly fee (e.g. Staff/Non-paying), skip showing them in debt list
                    if mfee <= 0: continue 

                    has_missing_payment = False
                    for month in self.filter_months_list:
                        # Check if this specific month/year is paid
                        cursor.execute("SELECT count(*) FROM monthly_fees WHERE user_id=? AND month=? AND year=? AND is_paid=1", 
                                       (uid, month, target_year))
                        if cursor.fetchone()[0] == 0:
                            has_missing_payment = True
                            break # Found a debt, show user
                    
                    if not has_missing_payment:
                        continue # User has paid all selected months, skip
                
                # Render
                full_name = f"{fname} {lname}"
                
                # Tag logic: Red if balance < 0 OR (user is in list because of missing quotas)
                debt_tag = ""
                if balance < 0 or (self.filter_months_list and has_missing_payment):
                     debt_tag = "has_debt"

                self.tree.insert("", "end", values=(uid, full_name, nif, email, mtype, phone, "❌"), tags=(debt_tag,))

    # --- EXPORT ---
    def export_list(self):
        """Exports the currently visible rows in Treeview to a text file."""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("Info", "A lista está vazia.")
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        default_name = f"Lista_Socios_{timestamp}.txt"
        
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name, title="Exportar Lista")
        if not path: return
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"LISTAGEM DE SÓCIOS - {datetime.now().strftime('%d/%m/%Y')}\n")
                f.write(f"Filtros: Época {self.year_var.get()}\n")
                f.write("="*80 + "\n")
                f.write(f"{'ID':<5} {'NOME':<30} {'NIF':<15} {'EMAIL':<30}\n")
                f.write("-" * 80 + "\n")
                
                count = 0
                for item in items:
                    vals = self.tree.item(item, "values")
                    # vals: uid, name, nif, email, type, phone, action
                    f.write(f"{vals[0]:<5} {vals[1]:<30} {vals[2]:<15} {vals[3]:<30}\n")
                    count += 1
                
                f.write("="*80 + "\n")
                f.write(f"Total Registos: {count}\n")
            
            messagebox.showinfo("Sucesso", "Lista exportada com sucesso.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    # --- EVENTS ---
    def on_double_click(self, event):
        try:
            item = self.tree.selection()
            if not item: return
            user_id = self.tree.item(item, "values")[0]

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()

            if user_data:
                # Store the dashboard window instance
                dash = user_dashboard.UserDashboard(self, user_data)
                
                # Wait for it to close
                self.wait_window(dash) 
                
                # Only refresh if the Main Window (self) is still open/alive
                if self.winfo_exists():
                    self.refresh_users()

        except (tk.TclError, Exception):
            # If the program is closing, ignore errors
            pass

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

    # --- DATABASE TOOLS & REPORTS ---
    def backup_database(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        default_name = f"Backup_CTPB_{timestamp}.db"
        target_path = filedialog.asksaveasfilename(defaultextension=".db", initialfile=default_name, title="Guardar Cópia")
        if not target_path: return
        try:
            src = sqlite3.connect(DB_NAME); dst = sqlite3.connect(target_path)
            with src, dst: src.backup(dst)
            src.close(); dst.close()
            messagebox.showinfo("Sucesso", f"Backup criado em:\n{target_path}")
        except Exception as e: messagebox.showerror("Erro", f"Falha: {e}")

    def restore_database(self):
        backup_path = filedialog.askopenfilename(title="Selecionar Cópia para Restaurar")
        if not backup_path: return
        if not messagebox.askyesno("PERIGO", "Isto irá SOBREPOR a base de dados atual.\nDeseja continuar?"): return
        try:
            src = sqlite3.connect(backup_path); dst = sqlite3.connect(DB_NAME)
            with src, dst: src.backup(dst)
            src.close(); dst.close()
            self.refresh_users()
            messagebox.showinfo("Sucesso", "Base de dados restaurada.")
        except Exception as e: messagebox.showerror("Erro", f"Falha: {e}")

    def reset_database(self):
        if not messagebox.askyesno("PERIGO", "Apagar TUDO?"): return
        if not messagebox.askyesno("CONFIRMAÇÃO", "Ação Irreversível. Continuar?"): return
        try:
            with get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.execute("DELETE FROM transactions"); conn.execute("DELETE FROM monthly_fees")
                conn.execute("DELETE FROM audit_logs"); conn.execute("DELETE FROM users"); conn.execute("DELETE FROM sqlite_sequence")
                conn.execute("PRAGMA foreign_keys = ON")
            self.refresh_users()
            messagebox.showinfo("Reiniciado", "Base de dados limpa.")
        except Exception as e: messagebox.showerror("Erro", f"Falha: {e}")

    def generate_monthly_report(self):
        self.ask_report("Mensal")

    def generate_yearly_report(self):
        self.ask_report("Anual")

    def ask_report(self, r_type):
        now = datetime.now()
        year = simpledialog.askinteger("Relatório", "Ano:", initialvalue=now.year)
        if not year: return
        
        if r_type == "Mensal":
            month = simpledialog.askinteger("Relatório", "Mês (1-12):", initialvalue=now.month)
            if not month: return
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
            title = f"RELATÓRIO MENSAL - {month:02d}/{year}"
            fname = f"Relatorio_Mensal_{month}_{year}.txt"
        else:
            start_date = f"{year}-01-01"
            end_date = f"{year+1}-01-01"
            title = f"RELATÓRIO ANUAL - {year}"
            fname = f"Relatorio_Anual_{year}.txt"
            
        self.build_and_save_report(title, start_date, end_date, fname)

    def build_and_save_report(self, title, start_date, end_date, default_filename):
        report_data = {}
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT amount, payment_method, notes FROM transactions WHERE payment_date >= ? AND payment_date < ? AND amount > 0 ORDER BY payment_date", (start_date, end_date))
                rows = cursor.fetchall()
            
            if not rows:
                messagebox.showinfo("Info", "Sem movimentos.")
                return

            total_overall = 0.0
            for amt, method, note in rows:
                cat = "Outros"
                n_low = note.lower()
                if "quota:" in n_low: cat = note 
                elif "aluguer" in n_low: cat = "Alugueres"
                elif "encordoamento" in n_low: cat = "Encordoamento"
                elif "bar" in n_low: cat = "Bar"
                
                if not method: method = "Indefinido"
                if cat not in report_data: report_data[cat] = {}
                if method not in report_data[cat]: report_data[cat][method] = 0.0
                report_data[cat][method] += amt
                total_overall += amt

            lines = ["="*40, title, "="*40, ""]
            for cat in sorted(report_data.keys()):
                lines.append(f"--- {cat}")
                for m, v in report_data[cat].items(): lines.append(f"{m:<20} : {v:>8.2f} €")
                lines.append("")
            lines.append("-" * 40); lines.append(f"TOTAL GERAL        : {total_overall:>8.2f} €"); lines.append("="*40)
            
            content = "\n".join(lines)
            path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_filename)
            if path:
                with open(path, "w", encoding="utf-8") as f: f.write(content)
                messagebox.showinfo("Sucesso", "Relatório guardado.")
            else:
                self.show_window(title, content)
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def show_window(self, title, content):
        win = tk.Toplevel(self); win.title(title); win.geometry("400x600")
        txt = scrolledtext.ScrolledText(win); txt.pack(fill="both"); txt.insert("end", content); txt.config(state="disabled")

if __name__ == "__main__":
    app = MainDashboard()
    app.mainloop()