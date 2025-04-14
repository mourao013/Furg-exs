import graphics as gf
import random as rd
win =  gf.GraphWin("Minha Janela", 400, 350)

c = gf.Circle(gf.Point(100,150),10)
cores = ['red','blue','green','orange','yellow','black']
c.setFill('red')
c.draw(win)
cont = 0
while True:

    onde_cliquei = (win.getMouse())
    print(onde_cliquei.getX(), onde_cliquei.getY())
    nova_bolinha = gf.Circle(onde_cliquei, 10)
    cor = rd.randint(0, len(cores)-1)
    nova_bolinha.setFill(cores[cor])
    nova_bolinha.draw(win)