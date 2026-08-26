# Economia original recuperada do Brasfoot

## Escopo e origem

As regras abaixo foram recuperadas por descompilação local do executável original fornecido no projeto. Elas descrevem o comportamento do jogo-base, não valores reais de mercado. Os pontos principais estão em `best.F.fJ()` (salário), `best.F.fK()` (valor do jogador), `best.ah.kK()` (folha), `best.ah.kJ()` (débito de folha) e `best.ah.kH()` (caixa de início de temporada).

## Salário do jogador

O jogo calcula e armazena um salário individual; a folha não é uma estimativa agregada. Em modo semanal, a fórmula descompilada é:

```text
base_divisão =
  países de faixa superior: D1=750, D2=550, D3=500, D4/D5=450
  demais países:             D1=600, D2=500, D3=450, D4/D5=400
  sem clube/sem divisão: 350

base_ajustada = base_divisão + 50, se nível do clube > 20
base_ajustada -= ajuste_por_categoria/posição

salário = força × 2 × round(0,5 × base_ajustada)
         + (força × 250, se estrela ou topo mundial)
         - ((idade - 32) × 300, somente se idade >= 32)

salário = máximo(salário, 500)
salário = round(salário × 1,4), se topo mundial
salário = round(salário × 0,1), se condição especial de empréstimo/contrato
salário = salário × 4, somente no modo mensal
```

Os ajustes por categoria no bytecode são `-70`, `-30`, `-40` e `-50` para quatro códigos internos. O SQL normalizado não preserva com segurança a mesma enumeração interna; a transposição deve usar um mapeamento explícito e testado de posição/categoria.

## Valor do jogador

O valor de mercado é separado do salário. O método original parte de `(força × 2)^2`, multiplica por uma faixa de nível do clube e aplica fatores de estrela, destaque, posição, status e idade. Portanto, **salário e valor de mercado não devem compartilhar uma única fórmula**.

## Folha e caixa

O clube mantém um campo de caixa persistido. A folha semanal é a soma dos salários individuais de profissionais e juniores; o método de cobrança debita exatamente essa soma do caixa.

O caixa de início de temporada é uma tabela por divisão, em vez de uma reserva calculada como número fixo de semanas de folha:

| Divisão | Caixa inicial (faixa A) | Caixa inicial (faixa B) |
|---|---:|---:|
| 0 | 3.500.000 | 2.000.000 |
| 1 | 15.000.000 | 12.000.000 |
| 2 | 12.000.000 | 10.000.000 |
| 3 | 10.000.000 | 7.000.000 |
| 4 | 3.500.000 | 3.000.000 |

O executável também aplica receitas e prêmios de competição em rotinas separadas. Comissão técnica e departamentos não aparecem como parte dessa fórmula clássica; no FutManager eles devem entrar como extensões explícitas da folha e manutenção semanal.

## Decisão de adaptação

O motor novo deve substituir a fórmula agregada provisória de folha de jogadores por salários individuais calculados e persistidos. Como o SQL normalizado não conserva todos os campos internos do executável, a primeira versão compatível deve declarar as aproximações: força derivada de CR1/CR2, posição normalizada, grupo econômico do país e nível de infraestrutura. A fórmula deve permanecer versionada para permitir recalibração sem alterar históricos já lançados.
