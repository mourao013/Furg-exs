'''
compras = ['banana', 'laranja', 'morango', 'abacate', 'omo']
print(compras)
print(compras[0:-1])
print(compras[0:3])
print(compras[1:3])
print(compras[2:])
print(compras[::2])
print(compras[::-1])
'''
'''
nome = input("nome: ")
print(nome[::-1])
lista = nome.split()#Separando em espaço
print(lista)
saida = ''
for item in lista:
        saida = saida + item[::-1] + ' '
print(saida)
'''
'''
#Cifra de cesár
n = int(input(''))
cont = 1
codigo = ''
while cont <= n :
    string = input('')
    pulo = int(input(''))
    for palavra in string:
        codigo = codigo + palavra[0] + ' '
    cont+=1
print(codigo)
'''