from smartcard.System import readers
from smartcard.util import toHexString

def test_nfc_reader():
    r = readers()
    if not r:
        print("Error: no NFC readers found")
        return

    reader = r[0]
    print(f"found reader: {reader}, waiting for connection")

    # establish connection
    try:
        connection = reader.createConnection()
        connection.connect()

        # FF CA 00 00 00 -> standard APDU command for ACR122U to get UID
        GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        data, sw1, sw2 = connection.transmit(GET_UID)

        if sw1 == 0x90 and sw2 == 0x00:
            print(f"card detected")
            print(f"UID: {toHexString(data)}")
        else:
            print(f"failed to read card: {sw1:02x} {sw2:02x}")

    except Exception as e:
        print(f"connection error: {e}")

if __name__ == "__main__":
    test_nfc_reader()
