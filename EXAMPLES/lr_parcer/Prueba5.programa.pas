program Programa_Pascal;
var
    a, b, c: integer;
    resultado: real;
    numero: integer;
    letra: char;
    edad: integer;
    promedio: real;
    inicial: char;
    activo: boolean;
    nombre: string;
    numeros: array[1..5] of integer;
    notas: array[1..3] of real;
    letras: array[1..4] of char;
    matriz: array[1..2, 1..3] of integer;
    i: integer;
    contador: integer;
    mayor, menor: integer;
    resultadoBool: boolean;
    valor: integer;
begin
    a := 10;
    b := 5;
    c := 2;
    resultado := a + b * c - (a / b);
    writeln('Resultado: ', resultado);

    numero := 3;
    case numero of
        1: letra := 'A';
        2: letra := 'B';
        3: letra := 'C';
        4: letra := 'D';
    else
        letra := '?';
    end;
    writeln('Numero: ', numero, ' Letra: ', letra);

    write('Nombre: ');
    readln(nombre);
    writeln('Nombre: ', nombre);
    writeln('numeros[', i, '] = ', numeros[i]);
    writeln('Numeros ingresados: ');

    for contador := 1 to 10 do
        writeln('Contador: ', contador);

    a := 8;
    b := 3;
    c := 5;

    if (a = 0) and (b = 0) and (c = 0) then
        writeln('Los tres numeros son 0')
    else
    begin
        if a >= b then
        begin
            if a >= c then
                mayor := a
            else
                mayor := c;
        end
        else
        begin
            if b >= c then
                mayor := b
            else
                mayor := c;
        end;

        if a <= b then
        begin
            if a <= c then
                menor := a
            else
                menor := c;
        end
        else
        begin
            if b <= c then
                menor := b
            else
                menor := c;
        end;

        writeln('Mayor: ', mayor);
        writeln('Menor: ', menor);
    end;

    numero := 7;

    if numero > 5 then
        resultadoBool := true
    else
        resultadoBool := false;

    if resultadoBool then
        writeln('Verdadero')
    else
        writeln('Falso');

    valor := 1;
    if valor = 1 then
        writeln('El valor es 1');
    if valor = 0 then
        writeln('El valor es 0');

    contador := 0;
    repeat
        contador := contador + 1;
        if contador = 4 then
            continue;
        writeln('Contador: ', contador);
    until contador >= 10;

    contador := 1;
    while contador <= 10 do
    begin
        if contador = 9 then
            break;
        writeln('Contador: ', contador);
        contador := contador + 1;
    end;

    writeln('Fin del ciclo');
end.