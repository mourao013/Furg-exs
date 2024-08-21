time1 = input("Digite um time: ")
time2 = input("Digite um time: ")
time3 = input("Digite um time: ")
time4 = input("Digite um time: ")
semi1 = (f"{time1} x {time2}")
semi2 = (f"{time3} x {time4}")
print(semi1)
print(semi2)
golstime1 = int(input(f"quantos gols fez o {time1}? "))
golstime2 = int(input(f"quantos gols fez o {time2}? "))
placar1 = (f"{semi1} : {golstime1} x {golstime2}")
print(placar1)
if golstime2 == golstime1:
    vencedor1 = int(input(f"quem venceu? ({time1}: 1 ou {time2}: 2)"))
    if (vencedor1 == 1):
        vencedor1 = time1
        print(f"{time1} avança")
    if(vencedor1 == 2):
        vencedor1 = time2
        print(f"{time2} avança")
if golstime1 > golstime2:
    vencedor1 = time1
    print(f"{time1} avança")
if golstime2 > golstime1:
    vencedor1 = time2
    print(f"{time2} avança")

golstime3 = int(input(f"quantos gols fez o {time3}?"))
golstime4 = int(input(f"quantos gols fez o {time4}?"))
placar2 = (f"{semi2}: {golstime3} x {golstime4}")
print(placar2)
if golstime3 == golstime4:
     vencedor2 = int(input(f"quem venceu? ({time3}: 1 ou {time4}: 2)"))
     if (vencedor2 == 1):
         print(f"{time3} avança")
     if (vencedor2 == 2):
         print(f"{time4} avança")
if golstime3 > golstime4:
    vencedor2 = (f"{time3}") 
    print(f"{time3} avança")
if golstime4 > golstime3:
    vencedor2 = (f"{time4}")
    print(f"{time4} avança")

final = (f"{vencedor1} X {vencedor2}")
print(f"A final será: {final}")

golsvencedor1 = int(input(f"quantos gols fez o {vencedor1}?"))
golsvencedor2 = int(input(f"quantos gols fez o {vencedor2}?"))
if golsvencedor1 > golsvencedor2:
    print(f"o Campeão foi {golsvencedor1}")
if golsvencedor2 > golsvencedor1:
        print(f"o campeão foi{golsvencedor2}")
if golsvencedor2 == golsvencedor1:
    campeao = int(input(f"quem venceu? ({vencedor1}: 1 ou {vencedor2}: 2)"))
    if (campeao == 1):
        print(f"o campeão é  o {vencedor1} ")
    if (campeao == 2):
        print(f"o campeão é o {vencedor2} ")