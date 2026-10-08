from menu import exibir_menu
from empreendimentos import listar_empreendimentos, consultar_empreendimento
from financiamento import simular_financiamento, criar_fluxo_pagamento
from visualizador import abrir_visualizador

def main():
    print("Bem-vindo ao Chatbot Imobiliário!")
    while True:
        opcao = exibir_menu()
        if opcao == '1':
            consultar_empreendimento()
        elif opcao == '2':
            simular_financiamento()
        elif opcao == '3':
            criar_fluxo_pagamento()
        elif opcao == '4':
            abrir_visualizador()
        elif opcao == '5':
            print("Saindo... Até logo!")
            break
        else:
            print("Opção inválida. Tente novamente.")

main()