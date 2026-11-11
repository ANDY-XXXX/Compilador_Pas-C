program Operaciones;

var
    a, b, c: integer;
    resultado: real;

begin
    a := 10;
    b := 5;
    c := 2;

    resultado := a + b * c - (a / b);

    writeln('Resultado: ', resultado);
end.