from app.adapters.camara.client import CamaraClient

cliente = CamaraClient(intervalo=0, tentativas=1)
dados = list(cliente.listar("partidos", itens=2))

print("Quantidade recebida:", len(dados))
for partido in dados:
    print(partido)
