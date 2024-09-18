'''
#ex1
lista = []
palavrasgrandes = []
segue = True
while segue:
    palavra = input("Digite: ")    
    if palavra == '0':
         break
    lista.append(palavra)
    if len(palavra) > 5:
         palavrasgrandes.append(palavra)
print(lista)
print(palavrasgrandes)
'''
'''
#ex2
num = []
nump = []
tamanho = int(input("Quantos numeros deseja testar? "))
while len(num) < tamanho:
    numero = int(input("Digite um numero: "))
    num.append(numero)
    if numero % 2 == 0:
        nump.append(numero)
print(num)
print(nump)
'''
'''
#EX3
l1 = []
l2 = []
juncao = []
while len(l1) < 5:
    p1 = input("Digite l1: ")
    l1.append(p1)
while len(l2)<5:
    p2 = input("Digite l2: ")
    l2.append(p2)


print(l1)
print(l2)
print(juncao)
'''