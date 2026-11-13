program Condicionales;

var
    edad, opcion: integer;

begin
    readln(edad);

    if edad >= 18 then
        writeln('Mayor de edad');

    if edad >= 18 then
        writeln('Mayor')
    else
        writeln('Menor');

    case opcion of
        1: writeln('Opcion uno');
        2: writeln('Opcion dos');
        3: writeln('Opcion tres');
    end;
end.