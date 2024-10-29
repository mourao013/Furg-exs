function soma(){
    var x = document.getElementById("v1");
    var y = document.getElementById("v2");
    soma = parseInt(x.value) + parseInt(y.value);
    alert(soma);
}
function sub(){
    var x = document.getElementById("v1");
    var y = document.getElementById("v2");
    sub = parseInt(x.value) - parseInt(y.value);
    alert(sub);
}
function mult(){
    var x = document.getElementById("v1");
    var y = document.getElementById("v2");
    mult = parseInt(x.value) * parseInt(y.value);
    alert(mult);
}
function div(){
    var x = document.getElementById("v1");
    var y = document.getElementById("v2");
    if (y.value == 0) {
        alert('impossivel dividir por 0')
    }
    else {
    div = parseInt(x.value) / parseInt(y.value);
    alert(div);
    }
}
