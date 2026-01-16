import os
import time
from utils import r, STREAM_KEY, publish_message

C_MGR, C_USR = "\033[94m", "\033[97m"
C_ANL, C_ARC = "\033[96m", "\033[95m"
C_COD, C_REV = "\033[92m", "\033[93m"
C_RST = "\033[0m"


def get_color(sender):
    if sender == "manager":
        return C_MGR
    if sender == "analyst":
        return C_ANL
    if sender == "architect":
        return C_ARC
    if sender == "coder":
        return C_COD
    if sender == "reviewer":
        return C_REV
    return C_RST


def listener(last_id="$"):
    print(f"\n{C_MGR}--- LIVE FEED ---{C_RST}\n")
    try:
        while True:
            messages = r.xread({STREAM_KEY: last_id}, count=10, block=1000)
            if messages:
                for msg in messages[0][1]:
                    last_id = msg[0]
                    data = msg[1]
                    sender = data.get("sender", "")
                    if sender == "user":
                        continue

                    color = get_color(sender)
                    clean = data.get("content", "").replace("\n", "\n│  ")
                    print(f"{color}┌─ [{sender.upper()}]")
                    print(f"│  {clean}")
                    print(f"└──────────────────────────────────────────────────{C_RST}")

                    if "PROJET TERMINÉ" in data["content"] or "DONE. Files" in data["content"]:
                        print(f"\n{C_COD}✅ FINISHED.{C_RST}\n")
                        return
    except KeyboardInterrupt:
        return


def main():
    os.system("clear")
    print(f"{C_MGR}=== SILENT FACTORY TERMINAL ==={C_RST}")
    while True:
        try:
            u_in = input(f"\n{C_USR}Cmd > {C_RST}")
            if u_in.lower() in ["q", "exit"]:
                break
            if not u_in.strip():
                continue
            publish_message("user", u_in, "order", status="DONE")
            listener(last_id="$")
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
