arq = open('alunos.csv', 'r') #r = read, usado tbm w = write e a = append



tudo = arq.readlines() 
print(tudo)
for item in tudo:
    print(item[:-1])
for item in tudo[1:]:
    colunas = item.split(';')
    print(colunas[1])

arq.close()