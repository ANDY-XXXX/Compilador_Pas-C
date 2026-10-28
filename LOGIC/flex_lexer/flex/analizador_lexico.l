%option noyywrap
%option yylineno
%option caseless

%{
    //Librerias, Declaracion de variables
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#define MAX 5000

/* Tira de tokens */
char lexemas[MAX][256];
char nombresToken[MAX][20];
int  lineasToken[MAX];
int  numTokens = 0;

/* Tabla de errores */
char descError[MAX][256];
int  lineaError[MAX];
int  numErrores = 0;

/* Tabla de simbolos */
char simbolos[MAX][256];
int  numSimbolos = 0;

int comentarioLinea = 1;

void agregarToken(const char *tipo);
void agregarError(const char *descripcion);
void agregarSimbolo(const char *nombre);
%}

/* Definiciones */
/* Expresiones Regulares */

identificador   [A-Za-z_][A-Za-z0-9]*
Entero          [0-9]+
Real            [0-9]+\.[0-9]+
Cadenas         '([^'\r\n]|")*'
Suma            \+
Resta           -
Multiplicacion  \*
Division        \/
Asignacion      :=
Menor           <
Menor_igual     <=
Mayor           >
Mayor_igual     >=
Igual           =
Diferente       <>
Rango           \.\.
Operador_Puntero  \^
Punto_Coma      ;
Coma            ,
Dos_Puntos      :
Parentesis_Izq  \(
Parentesis_Der  \)
Corchete_Izq    \[
Corchete_Der    \]
Punto           \.
Palabras_Reservada   program|var|begin|end|if|then|else|while|do|for|to|downto|repeat|until|function|procedure|integer|real|boolean|char|string|array|of|not|and|or|div|mod
Comentario      \{[^{}]*\}
Arroba          @
Ascii           #[0-9]+
Comentario_lin  \/\/.*

UTF8_2      [\xC2-\xDF][\x80-\xBF]
UTF8_3      [\xE0-\xEF][\x80-\xBF][\x80-\xBF]
UTF8_4      [\xF0-\xF4][\x80-\xBF][\x80-\xBF][\x80-\xBF]
UTF8_CHAR   ({UTF8_2}|{UTF8_3}|{UTF8_4})


/* Estados para los dos tipos de comentario de bloque*/
%x COMENTARIO_LLAVE
%x COMENTARIO_PARENTESIS

%%
    /* acciones */

    /* Espacios, tabs y saltos de linea: se ignoran */
[ \t\r\n]+              ;

    /* Comentario de una linea */
"//".*                   ;

    /* Comentario { ... } */
"{"                       { comentarioLinea = yylineno; BEGIN(COMENTARIO_LLAVE); }
<COMENTARIO_LLAVE>"}"      { BEGIN(INITIAL); }
<COMENTARIO_LLAVE><<EOF>>  { agregarError("comentario sin cerrar, falta }"); BEGIN(INITIAL); return 0; }
<COMENTARIO_LLAVE>(.|\n)   ;

    /* Comentario (* ... *) */
"(*"                      { comentarioLinea = yylineno; BEGIN(COMENTARIO_PARENTESIS); }
<COMENTARIO_PARENTESIS>"*)" { BEGIN(INITIAL); }
<COMENTARIO_PARENTESIS><<EOF>> { agregarError("comentario sin cerrar, falta *)"); BEGIN(INITIAL); return 0; }
<COMENTARIO_PARENTESIS>(.|\n)  ;

    /* Cadenas 'texto', con '' como comilla doble */
\'([^'\n]|\'\')*\'        { agregarToken("STRING"); }
\'([^'\n]|\'\')*           { agregarError("cadena sin cerrar, falta la comilla final"); }

    /* Literal de caracter: #65, #0, etc. */
"#"[0-9]+                 { agregarToken("ASCII"); }

    /* Operadores de dos caracteres */
":="                      { agregarToken("Asignacion"); }
"<="                      { agregarToken("Menor_igual"); }
">="                      { agregarToken("Mayor_igual"); }
"<>"                      { agregarToken("Comparacion"); }
".."                      { agregarToken("Rango"); }

    /* Numeros */
[0-9]+"."[0-9]+            { agregarToken("Real_LITERAL"); }
[0-9]+                      { agregarToken("Entero_LITERAL"); }

    /* Palabras Reservadas */
"program"       { agregarToken("PROGRAM"); }
"var"           { agregarToken("VAR"); }
"const"         { agregarToken("CONST"); }
"begin"         { agregarToken("BEGIN"); }
"end"           { agregarToken("END"); }
"if"            { agregarToken("IF"); }
"then"          { agregarToken("THEN"); }
"else"          { agregarToken("ELSE"); }
"while"         { agregarToken("WHILE"); }
"do"            { agregarToken("DO"); }
"for"           { agregarToken("FOR"); }
"to"            { agregarToken("TO"); }
"downto"        { agregarToken("DOWNTO"); }
"repeat"        { agregarToken("REPEAT"); }
"until"         { agregarToken("UNTIL"); }
"procedure"     { agregarToken("PROCEDURE"); }
"function"      { agregarToken("FUNCTION"); }
"integer"       { agregarToken("INTEGER"); }
"real"          { agregarToken("REAL"); }
"boolean"       { agregarToken("BOOLEAN"); }
"char"          { agregarToken("CHAR"); }
"string"        { agregarToken("STRING_TYPE"); }
"true"          { agregarToken("TRUE"); }
"false"         { agregarToken("FALSE"); }
"array"         { agregarToken("ARRAY"); }
"of"            { agregarToken("OF"); }
"and"           { agregarToken("AND"); }
"or"            { agregarToken("OR"); }
"not"           { agregarToken("NOT"); }
"div"           { agregarToken("DIV"); }
"mod"           { agregarToken("MOD"); }
"type"          { agregarToken("TYPE"); }
"record"        { agregarToken("RECORD"); }
"case"          { agregarToken("CASE"); }

    /* Identificadores: lo que no sea palabra reservada cae aqui */
[A-Za-z_][A-Za-z0-9_]*  { agregarToken("IDENTIFIER"); agregarSimbolo(yytext); }

    /* Operadores y simbolos de un caracter */
"+"   { agregarToken("Suma"); }
"-"   { agregarToken("Resta"); }
"*"   { agregarToken("Multiplicacion"); }
"/"   { agregarToken("Divsion"); }
"="   { agregarToken("Igual"); }
"<"   { agregarToken("Menor"); }
">"   { agregarToken("Mayor"); }
"("   { agregarToken("Parentesis_Izq"); }
")"   { agregarToken("Parentesis_Der"); }
"["   { agregarToken("Corchete_Izq"); }
"]"   { agregarToken("Corchete_Der"); }
":"   { agregarToken("Dos_Puntos"); }
";"   { agregarToken("Punto_Coma"); }
","   { agregarToken("Coma"); }
"."   { agregarToken("Punto"); }
"@"   { agregarToken("Arroba"); }
"^"   { agregarToken("Apuntador"); }

    /* Caracter UTF-8 completo */
{UTF8_CHAR} {
    char msg[280];

    snprintf(
        msg,
        sizeof(msg),
        "'%s' no pertenece al lenguaje",
        yytext
    );

    agregarError(msg);
}

    /* Cualquier otro caracter */
. {
    char msg[280];

    snprintf(
        msg,
        sizeof(msg),
        "'%s' no pertenece al lenguaje",
        yytext
    );

    agregarError(msg);
}

%%

// Procedimientos
// Auxiliares

void agregarToken(const char *tipo) {
    if (numTokens >= MAX) { fprintf(stderr, "Limite de tokens excedido (%d).\n", MAX); exit(2); }
    if (yyleng >= 256) { fprintf(stderr, "Lexema demasiado largo (maximo 255 bytes).\n"); exit(2); }
    strncpy(lexemas[numTokens], yytext, 255);
    strncpy(nombresToken[numTokens], tipo, 19);
    lineasToken[numTokens] = yylineno;
    numTokens++;
}

void agregarError(const char *descripcion) {
    if (numErrores >= MAX) { fprintf(stderr, "Limite de errores excedido (%d).\n", MAX); exit(2); }
    strncpy(descError[numErrores], descripcion, 255);
    lineaError[numErrores] = yylineno;
    numErrores++;
}

void agregarSimbolo(const char *nombre) {
    int i;
    for (i = 0; i < numSimbolos; i++) {
        if (strcasecmp(simbolos[i], nombre) == 0) {
            return;
        }
    }
    if (numSimbolos >= MAX) { fprintf(stderr, "Limite de simbolos excedido (%d).\n", MAX); exit(2); }
    strncpy(simbolos[numSimbolos], nombre, 255);
    numSimbolos++;
}

/* Escapa separadores para no romper las columnas del TSV. */
void escribirCelda(FILE *archivo, const char *texto) {
    for (; *texto; texto++) {
        if (*texto == '\t') fputs("\\t", archivo);
        else if (*texto == '\r') fputs("\\r", archivo);
        else if (*texto == '\n') fputs("\\n", archivo);
        else if (*texto == '\\') fputs("\\\\", archivo);
        else fputc(*texto, archivo);
    }
}

int main(int argc, char *argv[]) {
    char ruta[1024];
    int i;

    if (argc > 1) {
        if (strlen(argv[1]) >= sizeof(ruta)) { fprintf(stderr, "Ruta demasiado larga.\n"); return 1; }
        strcpy(ruta, argv[1]);
    } else {
        printf("Archivo Pascal (.pas): ");
        fgets(ruta, sizeof(ruta), stdin);
        ruta[strcspn(ruta, "\n")] = '\0';
    }

    yyin = fopen(ruta, "r");
    if (yyin == NULL) {
        printf("No se pudo abrir el archivo: %s\n", ruta);
        return 1;
    }

    yylex();
    fclose(yyin);

    /*  Tira de tokens  */
    FILE *ft = fopen("tiraTokens.tsv", "w");
    
    if (ft == NULL) {
        printf("No se pudo crear tiraTokens.tsv\n");
        return 1;
    }
    
    fprintf(ft, "Linea\tLexema\tToken\n");
    
    for (i = 0; i < numTokens; i++) {
        fprintf(ft, "%d\t", lineasToken[i]);
        escribirCelda(ft, lexemas[i]);
        fprintf(ft, "\t%s\n", nombresToken[i]);
    }
    
    fclose(ft);


    /*  Tabla de errores */
    FILE *fe = fopen("errores.tsv", "w");

    if (fe == NULL) {
        printf("No se pudo crear errores.tsv\n");
        return 1;
    }

    fprintf(fe, "Linea\tDescripcion\n");

    for (i = 0; i < numErrores; i++) {
        fprintf(
            fe,
            "%d\t%s\n",
            lineaError[i],
            descError[i]
        );
    }

    fclose(fe);


    /*  Tabla de simbolos  */
    FILE *fs = fopen("simbolos.tsv", "w");

    if (fs == NULL) {
        printf("No se pudo crear simbolos.tsv\n");
        return 1;
    }

    fprintf(fs, "Identificador\n");

    for (i = 0; i < numSimbolos; i++) {
        fprintf(
            fs,
            "%s\n",
            simbolos[i]
        );
    }

    fclose(fs);

    return 0;
}