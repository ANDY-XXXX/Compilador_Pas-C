program Calculadora;

const
    LIMITE = 100;

var
    a, b, resultado: integer;
    opcion: integer;
    continuar: boolean;

procedure MostrarMenu;
begin
    writeln('1. Sumar');
    writeln('2. Restar');
    writeln('3. Multiplicar');
end;

function Sumar(x: integer; y: integer): integer;
begin
    Sumar := x + y;
end;

begin
    continuar := true;

    while continuar do
    begin
        MostrarMenu;

        write('Selecciona una opcion: ');
        readln(opcion);

        case opcion of
            1:
            begin
                readln(a);
                readln(b);
                resultado := Sumar(a, b);
                writeln(resultado);
            end;

            2:
            begin
                readln(a);
                readln(b);
                resultado := a - b;
                writeln(resultado);
            end;

            3:
            begin
                readln(a);
                readln(b);
                resultado := a * b;
                writeln(resultado);
            end;
        end;

        if opcion = 0 then
            continuar := false;
    end;
end.