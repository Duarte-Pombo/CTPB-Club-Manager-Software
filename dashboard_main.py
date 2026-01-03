import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
import sqlite3
import user_dashboard
from datetime import datetime
import os

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
        # Using trace_add for Python 3.14 compatibility
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
        
        # Report Buttons
        tk.Button(bar_frame, text="📄 Relatório Mensal", command=self.generate_monthly_report, **btn_style).pack(side="left", padx=10, pady=10)
        tk.Button(bar_frame, text="📊 Relatório Anual", command=self.generate_yearly_report, **btn_style).pack(side="left", padx=10, pady=10)
        
        # Admin Buttons
        tk.Button(bar_frame, text="🔒 Cópia Segurança", command=self.backup_database, **btn_style).pack(side="right", padx=10, pady=10)
        tk.Button(bar_frame, text="🗑️ Reset Database", bg="#c0392b", fg="white", font=("Arial", 10, "bold"), bd=0, padx=15, pady=10, 
                  command=self.reset_database).pack(side="right", padx=10, pady=10)

    # --- MAIN LOGIC ---

    def refresh_users(self):
        for item in self.tree.get_children(): self.tree.delete(item)

        search_term = self.search_var.get().strip().lower()
        target_year = self.year_var.get()
        
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

    # --- DATABASE TOOLS (BACKUP & RESET) ---

    def backup_database(self):
        """Creates a safe copy of the running database."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        default_name = f"Backup_CTPB_{timestamp}.db"
        
        target_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
            initialfile=default_name,
            title="Guardar Cópia de Segurança"
        )

        if not target_path:
            return

        try:
            # Using SQLite Online Backup API (Safe for running apps)
            src = sqlite3.connect(DB_NAME)
            dst = sqlite3.connect(target_path)
            
            with src, dst:
                src.backup(dst)
            
            src.close()
            dst.close()
            messagebox.showinfo("Sucesso", f"Backup criado com sucesso em:\n{target_path}")

        except Exception as e:
            messagebox.showerror("Erro de Backup", f"Falha ao criar cópia: {e}")

    def reset_database(self):
        """Wipes all user data but keeps table structures."""
        # Warning 1
        if not messagebox.askyesno("PERIGO - APAGAR TUDO", 
                                   "ATENÇÃO:\nIsto irá apagar TODOS os sócios, transações e registos.\n\nDeseja realmente continuar?"):
            return

        # Warning 2 (Double confirmation)
        if not messagebox.askyesno("CONFIRMAÇÃO FINAL", 
                                   "Esta ação é IRREVERSÍVEL.\n\nTem a certeza absoluta que quer reiniciar a base de dados?"):
            return

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Turn off Foreign Keys to allow deletion in any order
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # Clear Tables
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM monthly_fees")
                cursor.execute("DELETE FROM audit_logs")
                cursor.execute("DELETE FROM users")
                
                # Reset Auto-Increment Counters (IDs start from 1 again)
                cursor.execute("DELETE FROM sqlite_sequence")
                
                # Note: We do NOT delete 'payment_types' as that is system config
                
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()

            self.refresh_users()
            messagebox.showinfo("Reiniciado", "A base de dados foi limpa com sucesso.")

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao limpar base de dados: {e}")

    # --- REPORT LOGIC ---

    def generate_monthly_report(self):
        now = datetime.now()
        year = simpledialog.askinteger("Relatório Mensal", "Ano:", initialvalue=now.year, minvalue=2020, maxvalue=2030)
        if not year: return
        month = simpledialog.askinteger("Relatório Mensal", "Mês (1-12):", initialvalue=now.month, minvalue=1, maxvalue=12)
        if not month: return

        start_date = f"{year}-{month:02d}-01"
        if month == 12: end_date = f"{year+1}-01-01"
        else: end_date = f"{year}-{month+1:02d}-01"

        title = f"RELATÓRIO MENSAL - {month:02d}/{year}"
        self.build_and_save_report(title, start_date, end_date, f"Relatorio_Mensal_{month}_{year}.txt")

    def generate_yearly_report(self):
        now = datetime.now()
        year = simpledialog.askinteger("Relatório Anual", "Ano:", initialvalue=now.year, minvalue=2020, maxvalue=2030)
        if not year: return

        start_date = f"{year}-01-01"
        end_date = f"{year+1}-01-01"

        title = f"RELATÓRIO ANUAL - {year}"
        self.build_and_save_report(title, start_date, end_date, f"Relatorio_Anual_{year}.txt")

    def build_and_save_report(self, title, start_date, end_date, default_filename):
        report_data = {}
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT amount, payment_method, notes, payment_date 
                    FROM transactions 
                    WHERE payment_date >= ? AND payment_date < ? AND amount > 0
                    ORDER BY payment_date
                """, (start_date, end_date))
                rows = cursor.fetchall()

            if not rows:
                messagebox.showinfo("Info", "Sem movimentos registados neste período.")
                return

            total_overall = 0.0

            for amt, method, note, date in rows:
                category = "Outros"
                note_lower = note.lower()

                if "quota:" in note_lower: category = note 
                elif "aluguer" in note_lower: category = "Alugueres"
                elif "encordoamento" in note_lower: category = "Encordoamento"
                elif "bar" in note_lower: category = "Bar"
                elif "pagamento:" in note_lower: category = "Regularização Dívidas"
                
                if not method: method = "Indefinido"

                if category not in report_data: report_data[category] = {}
                if method not in report_data[category]: report_data[category][method] = 0.0

                report_data[category][method] += amt
                total_overall += amt

            lines = []
            lines.append("="*40)
            lines.append(f"{title}")
            lines.append("="*40)
            lines.append("")

            sorted_cats = sorted(report_data.keys())
            for cat in sorted_cats:
                lines.append(f"--- {cat}")
                cat_total = 0.0
                for method, val in report_data[cat].items():
                    lines.append(f"{method:<20} : {val:>8.2f} €")
                    cat_total += val
                lines.append(f"{'Total':<20} : {cat_total:>8.2f} €")
                lines.append("")

            lines.append("-" * 40)
            lines.append(f"TOTAL GERAL        : {total_overall:>8.2f} €")
            lines.append("="*40)
            
            report_content = "\n".join(lines)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Guardar Relatório"
            )

            if file_path:
                with open(file_path, "w", encoding="utf-8") as f: f.write(report_content)
                messagebox.showinfo("Sucesso", f"Relatório guardado em:\n{file_path}")
            else:
                self.show_report_window(title, report_content)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")

    def show_report_window(self, title, content):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("400x600")
        txt = scrolledtext.ScrolledText(win, font=("Courier", 10))
        txt.pack(fill="both", expand=True)
        txt.insert("end", content)
        txt.config(state="disabled")

if __name__ == "__main__":
    app = MainDashboard()
    app.mainloop()