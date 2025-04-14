def mostra_nomes(lista):
    for linha in lista[1:]:
        uma_lista = linha.split(';')
        print(uma_lista[1])

def mais_novo(lista):
    novo = '10251231' #calibração inicial
    nome_do_novo = ''
    dt_original = ''
    for linha in lista[1:]: #[1:] ignora a segunda linha (cabeçalho)
        uma_lista = linha.split(';')
        data = uma_lista[2][:-1] #[:-1] elimina o '\n'
        lista_data = data.split('/')
        data_padrao = lista_data[2] + lista_data[1] + lista_data[0]
        if data_padrao > novo:
            novo = data_padrao
            nome_do_novo = uma_lista[1]
            dt_original = data
    print(nome_do_novo,novo)
arq = open('alunos.csv', 'r') #r = read, usado tbm w = write e a = append
tudo = arq.readlines()
mais_novo(tudo)
#mostra_nomes(tudo)
arq.close()
