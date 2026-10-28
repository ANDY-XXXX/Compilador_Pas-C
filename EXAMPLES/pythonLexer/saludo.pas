program Prueba;
var
  ifx, total: integer;
  nombre: string;
  promedio: real;

function Sumar(a, b: integer; var acumulado: integer): integer;
var
  resultado: integer;
begin
  resultado := a + b;
  acumulado := acumulado + resultado;
  Sumar := resultado;
end;

begin
  ifx := 5;
  total := 0;
  total := Sumar(ifx, 3, total);
  promedio := total / 2;

  if ifx <= total then
    nombre := 'ok'
  else
    nombre := 'no';

  y := 10 $ 2;
end.