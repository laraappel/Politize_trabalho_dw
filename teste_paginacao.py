from app.adapters.camara.client import CamaraClient

cliente = CamaraClient(intervalo=0, tentativas=1)
resposta = cliente.get("partidos", {"pagina": 1, "itens": 2})

print("Registros na primeira página:", len(resposta.get("dados", [])))
print("Metadados:", resposta.get("metadados"))
print("Links:", resposta.get("links"))
