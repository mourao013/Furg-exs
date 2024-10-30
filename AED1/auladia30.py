def tira_zero(num):
	num = str(num)
	saida = ''
	for algarismo in num:
		if algarismo != '0':
			saida += algarismo
	return saida


def soma_tira_zero():
	while True:	
		entrada = input("")
		entrada = entrada.split(' ')
		x = int(entrada[0])
		y = int(entrada[1])
		soma = x + y
		if soma == 0:
			return False
		print(tira_zero(soma))

soma_tira_zero()
