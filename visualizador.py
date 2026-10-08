import functools
import http.server
import json
import os
import threading
import webbrowser

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualizador")
_servidor = None


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def iniciar_servidor(porta_inicial=8000):
    global _servidor
    if _servidor is None:
        handler = functools.partial(_Silencioso, directory=PASTA)
        for porta in range(porta_inicial, porta_inicial + 10):
            try:
                _servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
                break
            except OSError:
                continue
        else:
            raise OSError("Nenhuma porta livre para o visualizador.")
        threading.Thread(target=_servidor.serve_forever, daemon=True).start()
    return f"http://localhost:{_servidor.server_address[1]}/"


def abrir_visualizador():
    with open(os.path.join(PASTA, "dados", "unidades.json"), encoding="utf-8") as f:
        unidades = {u["unidade"] for u in json.load(f)["unidades"]}
    codigo = input("Digite o código da unidade (ex.: T1-502) ou Enter para ver a fachada: ").strip().upper()
    if codigo and codigo not in unidades:
        print("Unidade não encontrada.")
        return
    url = iniciar_servidor()
    if codigo:
        url += f"?unidade={codigo}&tour=1"
    print(f"\nAbrindo o visualizador: {url}")
    print("(o visualizador fica no ar enquanto o chatbot estiver aberto)")
    webbrowser.open(url)
