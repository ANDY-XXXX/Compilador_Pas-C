program Operaciones;

var
    a, b, c: integer;
    resultado: real;
    valido: boolean;

begin
    a := 10;
    b := 20;
    c := 5;

    resultado := a + b * c;
    resultado := (a + b) / c;

    valido := a < b;
    valido := a < b and b > c;
    valido := a = b or c <> a;
end.