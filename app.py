import math
import csv

# Vetores para armazenar dados de cada cultura
soja_plantios = []
milho_plantios = []

def calcular_area(cultura): # Calcula a área das culturas
    if cultura == "soja":
        comprimento = float(input("Comprimento da área (m): "))
        largura = float(input("Largura da área (m): "))
        area = comprimento * largura
        return area, largura
    elif cultura == "milho":
        raio = float(input("Raio da área circular (m): "))
        area = math.pi * raio ** 2
        largura = raio * 2  # Diâmetro do círculo
        return area, largura
    else: # Caso o usuário insira uma cultura inválida
        print("Cultura inválida!")
        return None, None

def calcular_ruas(largura): # Calcula o número de ruas baseado na largura e no espaçamento
    print("\nComo deseja informar o número de ruas?")
    print("1. Calcular pelas dimensões e espaçamento")
    print("2. Informar manualmente")
    escolha = input("Escolha uma opção (1 ou 2): ").strip()
    if escolha == "1": # Cálculo automático
        espacamento = float(input("Espaçamento entre ruas (m): "))
        ruas = int(largura // espacamento)
        print(f"Número de ruas calculado: {ruas}")
    elif escolha == "2": # Entrada manual
        ruas = int(input("Informe o número de ruas: "))
    else:
        print("Opção inválida! Usando 0 ruas.")
        ruas = 0
    return ruas

def adicionar_plantio(): # Adiciona um novo plantio
    print("\nCulturas disponíveis: soja, milho")
    cultura = input("Digite a cultura do plantio: ").strip().lower() #lower() tranforma todo o texto em minúsculo, evitando erros de digitação
    area, largura = calcular_area(cultura)
    if area is None:
        return
    ruas = calcular_ruas(largura)
    insumo_por_rua = float(input("Quantidade de insumo por rua (L): "))
    insumo_total = ruas * insumo_por_rua
    registro = {
        'cultura': cultura,
        'area': area,
        'ruas': ruas,
        'insumo_por_rua': insumo_por_rua,
        'insumo_total': insumo_total
    }
    if cultura == "soja":
        soja_plantios.append(registro) # .append() adiciona o registro ao vetor
        print("Plantio de soja adicionado!")
    elif cultura == "milho":
        milho_plantios.append(registro)
        print("Plantio de milho adicionado!")
    else:
        print("Cultura inválida!")

def mostrar_plantios(): # Mostra todos os plantios registrados
    print("\n--- Plantios de Soja ---")
    if not soja_plantios:
        print("Nenhum plantio de soja registrado.")
    else:
        for i, p in enumerate(soja_plantios): # enumerate() retorna o índice e o valor do vetor
            print(f"{i}: Área = {p['area']:.2f} m² | Ruas = {p['ruas']} | Insumo/Rua = {p['insumo_por_rua']:.2f} L | Total = {p['insumo_total']:.2f} L")
    print("\n--- Plantios de Milho ---")
    if not milho_plantios:
        print("Nenhum plantio de milho registrado.")
    else:
        for i, p in enumerate(milho_plantios):
            print(f"{i}: Área = {p['area']:.2f} m² | Ruas = {p['ruas']} | Insumo/Rua = {p['insumo_por_rua']:.2f} L | Total = {p['insumo_total']:.2f} L")

def atualizar_plantio(): # Atualiza um plantio existente
    print("\nAtualizar qual cultura? (soja/milho)")
    cultura = input("Cultura: ").strip().lower()
    if cultura == "soja":
        if not soja_plantios:
            print("Nenhum plantio de soja registrado.")
            return
        mostrar_plantios()
        idx = int(input("Índice do plantio de soja para atualizar: "))
        if 0 <= idx < len(soja_plantios):
            area, largura = calcular_area("soja")
            ruas = calcular_ruas(largura)
            insumo_por_rua = float(input("Quantidade de insumo por rua (L): "))
            insumo_total = ruas * insumo_por_rua
            soja_plantios[idx] = { #idx é o índice do plantio a ser atualizado
                'cultura': 'soja',
                'area': area,
                'ruas': ruas,
                'insumo_por_rua': insumo_por_rua,
                'insumo_total': insumo_total
            }
            print("Plantio de soja atualizado!")
        else:
            print("Índice inválido.")
    elif cultura == "milho":
        if not milho_plantios:
            print("Nenhum plantio de milho registrado.")
            return
        mostrar_plantios()
        idx = int(input("Índice do plantio de milho para atualizar: "))
        if 0 <= idx < len(milho_plantios):
            area, largura = calcular_area("milho")
            ruas = calcular_ruas(largura)
            insumo_por_rua = float(input("Quantidade de insumo por rua (L): "))
            insumo_total = ruas * insumo_por_rua
            milho_plantios[idx] = {
                'cultura': 'milho',
                'area': area,
                'ruas': ruas,
                'insumo_por_rua': insumo_por_rua,
                'insumo_total': insumo_total
            }
            print("Plantio de milho atualizado!")
        else:
            print("Índice inválido.")
    else:
        print("Cultura inválida!")

def deletar_plantio(): # Deleta um plantio existente
    print("\nDeletar plantio de qual cultura? (soja/milho)")
    cultura = input("Cultura: ").strip().lower()
    if cultura == "soja":
        if not soja_plantios:
            print("Nenhum plantio de soja registrado.")
            return
        mostrar_plantios()
        idx = int(input("Índice do plantio de soja para deletar: "))
        if 0 <= idx < len(soja_plantios):
            del soja_plantios[idx]
            print("Plantio de soja removido!")
        else:
            print("Índice inválido.")
    elif cultura == "milho":
        if not milho_plantios:
            print("Nenhum plantio de milho registrado.")
            return
        mostrar_plantios()
        idx = int(input("Índice do plantio de milho para deletar: "))
        if 0 <= idx < len(milho_plantios):
            del milho_plantios[idx]
            print("Plantio de milho removido!")
        else:
            print("Índice inválido.")
    else:
        print("Cultura inválida!")

def exportar_csv():
    dados = soja_plantios + milho_plantios
    if not dados:
        print("Nenhum plantio registrado para exportar.")
        return
    try:
        with open('plantios.csv', 'w', newline='') as csvfile:  # Corrigido: adicionado string vazia
            campos = ['cultura', 'area', 'ruas', 'insumo_por_rua', 'insumo_total']
            writer = csv.DictWriter(csvfile, fieldnames=campos)
            writer.writeheader()
            for p in dados:
                writer.writerow({
                    'cultura': p['cultura'],
                    'area': p['area'],
                    'ruas': p['ruas'],
                    'insumo_por_rua': p['insumo_por_rua'],
                    'insumo_total': p['insumo_total']
                })
        print("Plantios exportados para plantios.csv")
    except Exception as e:
        print(f"Erro ao exportar para CSV: {e}")


def menu(): # Menu principal do sistema
    while True:
        print("\n--- Menu FarmTech Solutions ---\n")
        print("1. Adicionar plantio")
        print("2. Mostrar plantios")
        print("3. Atualizar plantio")
        print("4. Deletar plantio")
        print("5. Exportar plantios para CSV")
        print("6. Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            adicionar_plantio()
        elif opcao == "2":
            mostrar_plantios()
        elif opcao == "3":
            atualizar_plantio()
        elif opcao == "4":
            deletar_plantio()
        elif opcao == "5":
            exportar_csv()
        elif opcao == "6":
            print("Saindo do sistema. Até logo!")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu()