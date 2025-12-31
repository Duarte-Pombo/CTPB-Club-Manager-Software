import tkinter as tk
from tkinter import messagebox
import threading
import time
import users
from smartcard.System import readers
from smartcard.util import toHexString

class CTPB:
    def __init__(self, root):
        self.root = root
        self.root.title("Clube de Ténis de Paços de Brandão")
        self.root.geometry("400x300")

        # UI Elements
        self.label = tk.Label(root, text="À espera de um cartão..", font=("Arial", 14))
        self.label.pack(expand=True)
        self.status_var = tk.StringVar(value="Status do Leitor: A verificar...")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="blue")
        self.status_label.pack(side="bottom", pady=10)

        # Start the NFC listener thread
        self.nfc_thread = threading.Thread(target=self.nfc_listener, daemon=True)
        self.nfc_thread.start()

    def nfc_listener(self):
        """Background thread that waits for NFC card taps."""
        while True:
            try:
                r = readers()
                if not r:
                    self.status_var.set("Status do Leitor: Não encontrado")
                    time.sleep(2)
                    continue

                self.status_var.set(f"Status do Leitor: Connectado ({r[0]})")
                reader = r[0]
                connection = reader.createConnection()

                # Try to connect to a card
                try:
                    connection.connect()
                    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                    data, sw1, sw2 = connection.transmit(GET_UID)

                    if sw1 == 0x90 and sw2 == 0x00:
                        card_id = toHexString(data)
                        # Use root.after to trigger the popup safely from the main thread
                        self.root.after(0, self.show_card_popup, card_id)

                        # Sleep briefly to avoid reading the same tap multiple times
                        time.sleep(3)
                except:
                    # No card present, just loop again
                    pass

            except Exception as e:
                print(f"Thread Error: {e}")

            time.sleep(0.5)

    def show_card_popup(self, card_id):
        """Checks database and opens either Info or Registration."""
        user_data = users.get_user_by_card(card_id)

        if user_data:
            # User exists: Show info
            # user_data indices match your table: 2=first_name, 3=last_name, 9=balance
            name = f"{user_data[2]} {user_data[3]}"
            balance = user_data[9]
            messagebox.showinfo("Sócio Reconhecido",
                                f"Bem-vindo, {name}!\nSaldo Atual: {balance}€")
        else:
            # New User: Open registration window
            if messagebox.askyesno("Desconhecido", f"Cartão {card_id} não registado.\nDeseja registar novo sócio?"):
                users.UserRegistrationWindow(self.root, card_id)

if __name__ == "__main__":
    root = tk.Tk()
    app = CTPB(root)
    root.mainloop()
