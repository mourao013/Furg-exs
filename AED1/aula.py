# def binario(x):
    
#     binario = ''
#     while x > 0:
#         resto = x%2
#         x = x//2
#         binario  =  str(resto) + binario 
    
#     return( binario)

x = input("Digite: ")

decimal =''

for algarismo in x:
    conv = (2**x[0])*algarismo
    decimal = str(conv) + decimal
print(decimal)
