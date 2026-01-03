import tkinter as tk
from tkinter import messagebox
import threading
import time
import users
import user_dashboard
from dashboard_main import MainDashboard # Importing the new UI
from smartcard.System import readers
from smartcard.util import toHexString

class CTPB_App:
    def __init__(self):
        # Initialize the Main Dashboard Window
        self.app = MainDashboard()
        
        # Start the NFC listener in a separate thread
        self.nfc_thread = threading.Thread(target=self.nfc_listener, daemon=True)
        self.nfc_thread.start()

    def run(self):
        self.app.mainloop()

    def nfc_listener(self):
        """Background thread that waits for NFC card taps."""
        print("NFC Listener Started...")
        while True:
            try:
                r = readers()
                if not r:
                    time.sleep(2)
                    continue

                reader = r[0]
                connection = reader.createConnection()

                try:
                    connection.connect()
                    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                    data, sw1, sw2 = connection.transmit(GET_UID)

                    if sw1 == 0x90 and sw2 == 0x00:
                        card_id = toHexString(data)
                        print(f"Card Detected: {card_id}")
                        
                        # Trigger UI action safely from the main thread
                        self.app.after(0, self.handle_card_tap, card_id)

                        # Prevent multiple reads of the same tap
                        time.sleep(3)
                except Exception:
                    pass

            except Exception as e:
                print(f"NFC Error: {e}")

            time.sleep(0.5)

    def handle_card_tap(self, card_id):
        """Logic to handle what happens when a card is scanned."""
        user_data = users.get_user_by_card(card_id)

        if user_data:
            # Check if user is active (Soft Delete check)
            # user_data[10] is 'is_active' based on schema order
            if not user_data[10]: 
                messagebox.showwarning("Aviso", "Este cartão pertence a um sócio inativo.")
                return

            # Open Dashboard on top of Main Window
            user_dashboard.UserDashboard(self.app, user_data)
            # Refresh main list after closing dashboard (in case payments were made)
            self.app.refresh_users()
        else:
            if messagebox.askyesno("Desconhecido", f"Cartão {card_id} não registado.\nDeseja registar?"):
                users.UserRegistrationWindow(self.app, card_id)
                self.app.refresh_users()

if __name__ == "__main__":
    program = CTPB_App()
    program.run()