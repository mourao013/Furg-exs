function media(){
    n1 = parseFloat(document.getElementById('n1').value);
    n2=parseFloat(document.getElementById('n2').value);
    n3=parseFloat(document.getElementById('n3').value);
    n4=parseFloat(document.getElementById('n4').value);
    med= (n1+n2+n3+n4) / 4
    if (med >= 7){
        alert('Aprovado')
    }
    else
        alert('reprovado')

}