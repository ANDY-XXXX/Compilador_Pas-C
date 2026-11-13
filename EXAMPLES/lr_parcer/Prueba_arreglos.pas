program Arreglos;

var
    numeros: array [1..10] of integer;
    i: integer;

begin
    for i := 1 to 10 do
        numeros[i] := i * 2;

    writeln(numeros[1]);
    writeln(numeros[5]);
end.