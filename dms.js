function show(str){
    var regex = /^[+-]?[0-9]+(\.[0-9]+)?$/;
    var n = document.getElementById('n').value
    if (regex.test(n)){
        alert('é um número válido');
    }
    else{
        alert("Não é um número válido")
    }
}
