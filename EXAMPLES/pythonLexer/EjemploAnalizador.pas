program EjemploPruebaAnalizadorLexico;

type
  TPersona = record
    nombre: array[1..20] of Char;
    edad: Integer;
  end;

var
  // declaraciones de varios tipos de variables
  ~
  a, b: Char;
  cad: array[1..30] of Char;
  `
  { comentario
    de bloque }
  aptr: ^Integer;
  vec: array[1..10] of Integer;
  categ: Integer;
  aVecPtr: array[1..3] of ^Integer;
  matriz: array[1..2, 1..2] of Integer;
  vecFloat: array[1..3] of Real;
  sueldo, nsueldo: Real;
  i, j, n, pot: Integer;
  suma: Real;
  calif: Integer;
  persona: TPersona;

function funcion(x, y: Real): Real;
var
  matrizLocal: array[1..2, 1..2] of Integer;
  cx, cy: Char;
begin
  cx := ' ';
  cy := #0;
  if x <> y then
    matrizLocal[i, j] := 0;
  funcion := x + y;
end;

begin
  categ := 2;
  vecFloat[1] := 2.3;
  vecFloat[2] := 5.0;
  vecFloat[3] := 3.1;

  persona.nombre := 'Juan Perez';
  persona.edad := 20;

  aptr := @categ;
  aptr^ := aptr^ + 1;

  Write('Teclea dos numeros enteros: ');
  ReadLn(a, b);

  categ := categ mod 2;
  if categ = 0 then
  begin
    WriteLn(categ, ' es par');
  end
  else
  begin
    categ := categ - 1;
    cad := 'hola';
  end;

  case categ of
    1: nsueldo := sueldo * 1.15;
    2: nsueldo := funcion(2.1, 3.2);
  else
    WriteLn(funcion(2, 3):0:2);
  end;

  for i := 5 downto 0 do
    WriteLn(i);

  for i := 0 to n do
  begin
    pot := 1;
    for j := 0 to i - 1 do
      pot := pot * 2;
    suma := suma + 1 / pot;
  end;

  if (n > 0) and (pot >= 1) then
    WriteLn('n es mayor que cero');

  i := 0;
  while (i <= 4) and not (suma = 0) do
  begin
    suma := suma + 2;
    i := i + 1;
  end;

  i := 1;
  repeat
    suma := suma * 2;
    i := i - 1;
  until (i <= 0) or (calif <> 0);
end.