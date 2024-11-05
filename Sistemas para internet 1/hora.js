function tempo(){

    var dataAtual = new Date();
    
    horas = dataAtual.getHours();
    
    minutos = dataAtual.getMinutes();
    
    segundos = dataAtual.getSeconds();

    if(horas < 12){
        document.write("Bom Dia, são " + horas + ":" + minutos + ":" + segundos)
    }
    else if(horas < 19){
        document.write("Boa Tarde")
    }
    else{
        document.write("Boa Noite")

    }
}