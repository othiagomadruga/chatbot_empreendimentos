empreendimentos = [
    {"nome": "Empreendimento A", "valor": 300000.00, "detalhes": "Apartamento de 2 quartos, 70m², com varanda."},
    {"nome": "Empreendimento B", "valor": 400000.00, "detalhes": "Apartamento de 3 quartos, 90m², com área de lazer."},
    {"nome": "Empreendimento C", "valor": 600000.00, "detalhes": "Casa de 4 quartos, 150m², com jardim."}
]

def listar_empreendimentos():
    print("\nLista de Empreendimentos:")
    for i, emp in enumerate(empreendimentos, 1):
        print(f"{i}. {emp['nome']} - R$ {emp['valor']:.2f}")

def consultar_empreendimento():
    listar_empreendimentos()
    try:
        escolha = int(input("Selecione o número do empreendimento: "))
        if 1 <= escolha <= len(empreendimentos):
            emp = empreendimentos[escolha - 1]
            print(f"\nDetalhes do {emp['nome']}:")
            print(f"Valor: R$ {emp['valor']:.2f}")
            print(f"Descrição: {emp['detalhes']}")
        else:
            print("Escolha inválida.")
    except ValueError:
        print("Por favor, digite um número válido.")