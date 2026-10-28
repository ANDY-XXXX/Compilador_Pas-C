program PruebaCompleta;

{ Comentario de bloque con llaves }
(* Comentario de bloque con parentesis y asteriscos *)
// Comentario de una sola linea

const
  MAXIMO = 10;
  PI = 3.1416;
  LETRA_A = #65;

type
  RangoEnteros = 1..10;
  ArregloEnteros = array[1..5] of integer;
  Persona = record
    edad: integer;
    inicial: char;
  end;

var
  contador, resultado, residuo, variable_2: integer;
  numeroReal: real;
  activo, condicion: boolean;
  letra: char;
  mensaje, textoConComilla: string;
  numeros: array[1..5] of integer;
  matriz: array[1..2, 1..3] of real;
  personaActual: Persona;
  puntero: ^integer;
  doblePuntero: ^^integer;

procedure MostrarMensaje(texto: string);
begin
  writeln(texto);
end;

function Sumar(a, b: integer): integer;
begin
  Sumar := a + b;
end;

begin
  contador := 5;
  variable_2 := 100;
  numeroReal := 12.75;
  activo := true;
  condicion := false;
  letra := #65;
  mensaje := 'Hola mundo';
  textoConComilla := 'Pascal dice: ''Hola''';

  resultado := contador + 3 - 2 * 4 / 2;
  resultado := 17 div 5;
  residuo := 17 mod 5;

  numeros[1] := 10;
  numeros[2] := 20;
  matriz[1, 2] := 4.50;

  personaActual.edad := 20;
  personaActual.inicial := #76;

  puntero := @contador;
  puntero^ := 25;
  doblePuntero := @puntero;

  if contador < MAXIMO then
    MostrarMensaje('contador es menor')
  else
    MostrarMensaje('contador no es menor');

  if contador <= 10 then
    condicion := true;

  if contador > 0 then
    condicion := true;

  if contador >= 5 then
    condicion := true;

  if contador = 5 then
    condicion := true;

  if contador <> 0 then
    condicion := true;

  if activo and condicion then
    MostrarMensaje('ambas condiciones son verdaderas');

  if activo or condicion then
    MostrarMensaje('alguna condicion es verdadera');

  if not condicion then
    MostrarMensaje('condicion negada');

  while contador < 8 do
  begin
    contador := contador + 1;
  end;

  for contador := 1 to 5 do
  begin
    numeros[contador] := contador * 2;
  end;

  for contador := 5 downto 1 do
  begin
    resultado := resultado + contador;
  end;

  repeat
    contador := contador - 1;
  until contador = 0;

  case residuo of
    0: MostrarMensaje('residuo cero');
    1: MostrarMensaje('residuo uno');
  end;

  resultado := Sumar(contador, MAXIMO);

  // Las siguientes lineas producen errores lexicos intencionales.
  // Sirven para comprobar que la tabla de errores se genere y la ejecucion continue.
  resultado := 10 $ 2;
  resultado := 10 & 2;
  resultado := 10 ! 2;
  resultado := 10 á 2;
  mensaje := 'Esta cadena no tiene comilla final

  MostrarMensaje('El analizador continuo despues de los errores');
end.

{ Comentario sin cerrar intencional para probar el error de fin de archivo
