#correção exercicios lista
'''
#1- cria uma função que recebe uma lista e retorna uma lista apenas com os string mais e 5 caracteres

def filtra(lista):
    saida = []
    for item in lista:
        if len(item) > 5:
            saida.append(item)
    return saida

lista_entrada = ['Davi', 'Caio', 'Cauã', 'Julia', 'Stefani', 'Luis Eduardo', 'Felipe']

lista_saida = filtra(lista_entrada)

print(lista_saida)

segue = True
lista_entrada = []
while segue:
    novo = input("Nome: ")
    if novo == '':
        segue = False
    else:
        lista_entrada.append(novo)

lista_saida = filtra(lista_entrada)
print(lista_saida)
'''
'''
#3 - Uma função que recebe duas listas e retona uma lsita com os elementos em comum 

L1 = ['A','B','C','D','E']
L2 = ['F', 'A', 'D', '8']
comum =[]
for item in L1:
    if item in L2:
        comum.append(item)

print(comum)

#3 só que com funções
def contem(teste,lista):
    for item in lista:
        if teste == item: #Achei o elemento!!
            return True
    return False #Ultimo return sempre na mesma linha do for, se não da problema


def em_comum(L1,L2):
    comum = []
    for item in L1:
        if contem(item,L2):
            comum.append(item)
    return(comum)

L1 = ['A','B','C','D','E']
L2 = ['F', 'A', 'D', '8','E']
comum = em_comum(L1,L2)
print(comum)

'''

#dada uma lista, escreva um programa que conte quantos elementos unicos (diferentes) estao na lista

def qtos_diferentes(lista):
    unicos = []
    for item in lista:
        if item not in unicos:
            unicos.append(item)
    return len(unicos)


def qtos_unicos(lista):

    unicos = []
    cont = 1 

    if lista[0] not in lista[1:]:
        unicos.append(lista[0])

    while cont < len(lista)-1:
        
        item = lista[cont]
        pra_traz = lista[:cont]
        pra_frente = lista[cont+1:]
        
        if item not in pra_traz and item not in pra_frente:
            unicos.append(item)
        cont = cont+1

    if lista[cont] not in lista[:cont]:
        unicos.append(lista[cont])
    return(len(unicos))

lista = [0,5,3,7,9,5,3,1,1,3,1,2,3,4,2,4,6,3,9,5,3,6,6,1978,2024,1000,2024,2025,72221,2,7]

print ('Diferentes: ' + str(qtos_diferentes(lista)))

print (f"Unicos: " + str(qtos_unicos(lista)))




#retorna o indice que esta o elemento. Se for -1 é pq não tem lista
def onde_esta(item,lista):
    cont = 0
    while cont < len(lista):
        if item == lista[cont]:
            return(cont)
        cont+=1
    return (-1)#não achei

def qtos_unicos2(lista):
    elementos = []
    quantidade = []
    
    for item in lista:
        if item in elementos:
            indice = onde_esta(item,elementos)
            quantidade[indice] +=1
        else:
            elementos.append(item)
            quantidade.append(1)

    quantos_unicos = 0
    for item in quantidade:
        if item == 1:
            quantos_unicos +=1
    return(quantos_unicos(lista))

lista = [0,5,3,7,9,5,3,1,1,3,1,2,3,4,2,4,6,3,9,5,3,6,6,1978,2024,1000,2024,2025,72221,2,7]
print(lista)
print ('Diferentes: ' + str(qtos_diferentes(lista)))
print ("Unicos: " + str(qtos_unicos(lista)))
print ("unicos 2 : " + str(qtos_unicos2(lista)))