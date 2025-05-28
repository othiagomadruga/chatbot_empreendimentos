def calcular_valor_financiavel(parcela, taxa_mensal, num_meses):
    if taxa_mensal == 0:
        return parcela * num_meses
    else:
        return parcela * (1 - (1 + taxa_mensal) ** -num_meses) / taxa_mensal

def simular_financiamento():
    print("\nSimulação de Financiamento")
    try:
        salario = float(input("Digite seu salário bruto: R$ "))
        valor_entrada = float(input("Digite o valor de entrada: R$ "))
        fgts = float(input("Digite o valor do FGTS: R$ "))
        taxa_anual = 0.11  # 11% ao ano, baseado em dados de 2025
        num_anos = 30
        taxa_mensal = taxa_anual / 12
        num_meses = num_anos * 12
        parcela_maxima = 0.3 * salario
        valor_financiavel = calcular_valor_financiavel(parcela_maxima, taxa_mensal, num_meses)
        total_disponivel = valor_entrada + fgts
        valor_max_imovel = valor_financiavel + total_disponivel
        print(f"\nCom base no seu salário de R$ {salario:.2f}, você pode pagar uma parcela de até R$ {parcela_maxima:.2f} por mês.")
        print(f"Com uma taxa de juros de {taxa_anual*100:.2f}% ao ano e prazo de {num_anos} anos, você pode financiar até R$ {valor_financiavel:.2f}.")
        print(f"Considerando seu valor de entrada de R$ {valor_entrada:.2f} e FGTS de R$ {fgts:.2f}, você pode adquirir um imóvel de até R$ {valor_max_imovel:.2f}.")
    except ValueError:
        print("Por favor, digite valores numéricos válidos.")

def criar_fluxo_pagamento():
    try:
        valor_entrada = float(input("Digite o valor de entrada: R$ "))
        num_parcelas = 24
        valor_parcela = valor_entrada / num_parcelas
        print(f"\nFluxo de pagamento para entrada de R$ {valor_entrada:.2f} em {num_parcelas} parcelas:")
        for i in range(1, num_parcelas + 1):
            print(f"Parcela {i}: R$ {valor_parcela:.2f}")
    except ValueError:
        print("Por favor, digite um valor numérico válido.")