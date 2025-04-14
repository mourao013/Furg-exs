from graphics import *
import csv
import webbrowser

class Estoque:  # Essa classe gerencia as operações de estoque, como carregar, salvar, adicionar e reduzir itens.
    def __init__(self, arquivo_csv):
        self.estoque_csv = arquivo_csv
        self.estoque = self.carregar_estoque()

    def carregar_estoque(self):  # Carrega os dados do estoque a partir de um arquivo CSV e retorna um dicionário com os produtos e suas quantidades.
        estoque = {}
        try:
            with open('estoque.csv', mode='r') as arquivo:
                leitor = csv.reader(arquivo)
                next(leitor)
                for linha in leitor:
                    Id, Nome, Valor , quantidade  = linha
                    estoque[Id] = estoque[Nome] = estoque[float(Valor)] = int(quantidade)
        except FileNotFoundError:
            pass
        return estoque

    def salvar_estoque(self):  # Salva o estado atual do estoque em um arquivo CSV, garantindo persistência dos dados.
        with open('self-estoque.csv', mode='w', newline='') as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(["Produto", "Quantidade, Valor"])
            for produto, quantidade, valor in self.estoque.items():
                escritor.writerow([produto, quantidade, valor])

    def adicionar_item(self, produto, quantidade):  # Adiciona um novo produto ou atualiza a quantidade de um produto existente no estoque.
        if produto in self.estoque:
            self.estoque[produto] += quantidade
        else:
            self.estoque[produto] = quantidade
        self.salvar_estoque()

    def reduzir_item(self, produto, quantidade):  # Reduz a quantidade de um produto no estoque, verificando se há estoque suficiente.
        if produto in self.estoque and self.estoque[produto] >= quantidade:
            self.estoque[produto] -= quantidade
            self.salvar_estoque()
            return True
        return False

    def gerar_html_estoque(self):  # Gera um arquivo HTML que lista os itens do estoque e abre o arquivo no navegador padrão.
        html = "<html><body><h1>Lista de Estoque</h1><ul>"
        for produto, quantidade in self.estoque.items():
            html += f"<li>{produto}: {quantidade}</li>"
        html += "</ul></body></html>"
        with open("estoque.html", "w") as arquivo:
            arquivo.write(html)
        webbrowser.open("estoque.html")

estoque = Estoque("estoque.csv")

def janela_principal():  # Cria a janela principal do sistema com quatro botões para acessar as funcionalidades de estoque.
    win = GraphWin("Sistema de Estoque", 400, 400)
    win.setBackground("lightgray")

    titulo = Text(Point(200, 50), "Sistema de Gestão de Estoque")
    titulo.setSize(16)
    titulo.draw(win)

    btn_visualizar = Rectangle(Point(100, 100), Point(300, 150))
    btn_visualizar.setFill("lightblue")
    btn_visualizar.draw(win)
    txt_visualizar = Text(btn_visualizar.getCenter(), "Visualizar Estoque")
    txt_visualizar.draw(win)

    btn_comprar = Rectangle(Point(100, 160), Point(300, 210))
    btn_comprar.setFill("lightgreen")
    btn_comprar.draw(win)
    txt_comprar = Text(btn_comprar.getCenter(), "Comprar Itens")
    txt_comprar.draw(win)

    btn_html = Rectangle(Point(100, 220), Point(300, 270))
    btn_html.setFill("lightcoral")
    btn_html.draw(win)
    txt_html = Text(btn_html.getCenter(), "Visualizar Estoque (HTML)")
    txt_html.draw(win)

    btn_adicionar = Rectangle(Point(100, 280), Point(300, 330))
    btn_adicionar.setFill("lightyellow")
    btn_adicionar.draw(win)
    txt_adicionar = Text(btn_adicionar.getCenter(), "Adicionar Novo Item")
    txt_adicionar.draw(win)

    while True:
        click = win.getMouse()
        if btn_visualizar.getP1().getX() <= click.getX() <= btn_visualizar.getP2().getX() and \
           btn_visualizar.getP1().getY() <= click.getY() <= btn_visualizar.getP2().getY():
            visualizar_estoque()
        elif btn_comprar.getP1().getX() <= click.getX() <= btn_comprar.getP2().getX() and \
             btn_comprar.getP1().getY() <= click.getY() <= btn_comprar.getP2().getY():
            comprar_itens()
        elif btn_html.getP1().getX() <= click.getX() <= btn_html.getP2().getX() and \
             btn_html.getP1().getY() <= click.getY() <= btn_html.getP2().getY():
            estoque.gerar_html_estoque()
        elif btn_adicionar.getP1().getX() <= click.getX() <= btn_adicionar.getP2().getX() and \
             btn_adicionar.getP1().getY() <= click.getY() <= btn_adicionar.getP2().getY():
            adicionar_item()

def visualizar_estoque():  # Abre uma janela que exibe a lista de produtos e suas quantidades no estoque.
    win = GraphWin("Visualizar Estoque", 300, 300)
    win.setBackground("white")

    y = 20
    for  produto, valor in estoque.estoque.items():
        texto = Text(Point(150, y), f"{produto}, {valor}")
        texto.draw(win)
        y += 20

def comprar_itens():  # Abre uma janela para permitir ao usuário reduzir a quantidade de itens no estoque ao realizar uma compra.
    win = GraphWin("Comprar Itens", 300, 300)
    win.setBackground("white")

    Text(Point(150, 50), "Produto:").draw(win)
    entrada_produto = Entry(Point(150, 80), 20)
    entrada_produto.draw(win)

    Text(Point(150, 110), "Quantidade:").draw(win)
    entrada_quantidade = Entry(Point(150, 140), 20)
    entrada_quantidade.draw(win)

    Text(Point(150, 170), "Preço:").draw(win)
    entrada_preco = Entry(Point(150, 200), 20)
    entrada_preco.draw(win)
    
    btn_comprar = Rectangle(Point(100, 220), Point(200, 260))
    btn_comprar.setFill("lightblue")
    btn_comprar.draw(win)
    Text(btn_comprar.getCenter(), "Comprar").draw(win)

    while True:
        click = win.getMouse()
        if btn_comprar.getP1().getX() <= click.getX() <= btn_comprar.getP2().getX() and btn_comprar.getP1().getY() <= click.getY() <= btn_comprar.getP2().getY():
            produto = entrada_produto.getText()
            quantidade = int(entrada_quantidade.getText())
            break
    if estoque.reduzir_item(produto, quantidade):
        Text(Point(150, 260), "Compra realizada com sucesso!").draw(win)
    else:
        Text(Point(150, 260), "Erro: Produto ou quantidade inválida.").draw(win)
    
    

def adicionar_item():  # Abre uma janela para permitir ao usuário adicionar novos itens ou atualizar a quantidade de itens existentes no estoque.
    win = GraphWin("Adicionar Item", 300, 300)
    win.setBackground("white")

    Text(Point(150, 50), "Produto:").draw(win)
    entrada_produto = Entry(Point(150, 80), 20)
    entrada_produto.draw(win)

    Text(Point(150, 110), "Quantidade:").draw(win)
    entrada_quantidade = Entry(Point(150, 140), 20)
    entrada_quantidade.draw(win)

    Text(Point(150, 170), "Valor:").draw(win)
    entrada_valor = Entry(Point(150, 200), 20)
    entrada_valor.draw(win)
    
    btn_adicionar = Rectangle(Point(100, 230), Point(200, 270))
    btn_adicionar.setFill("lightgreen")
    btn_adicionar.draw(win)
    Text(btn_adicionar.getCenter(), "Adicionar").draw(win)

    while True:
        click = win.getMouse()
        if btn_adicionar.getP1().getX() <= click.getX() <= btn_adicionar.getP2().getX() and btn_adicionar.getP1().getY() <= click.getY() <= btn_adicionar.getP2().getY():
            break
    
    produto = entrada_produto.getText()
    quantidade = int(entrada_quantidade.getText())
    estoque.adicionar_item(produto, quantidade)

    Text(Point(150, 260), "Item adicionado com sucesso!").draw(win)
    
    win.close()

if __name__ == "__main__":
    janela_principal()
