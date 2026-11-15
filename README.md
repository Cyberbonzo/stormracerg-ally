# Storm Racer G — ROG Ally / Bazzite

Versão 0.1.0. Integração para jogar uma cópia própria de Storm Racer G (2013) no ROG Ally com Bazzite: Proton 11, entrada analógica e atalho Steam.

Este repositório contém somente código próprio e documentação. Traga sua própria cópia do jogo. Nenhuma ROM, DLL, arte, vídeo, captura ou save é distribuído aqui. Projeto independente, sem afiliação aos titulares do jogo.

## Instalação

Requer Python 3 com Pillow, SDL2, Fontconfig, cabextract, xdotool e Proton 11.0 já disponíveis. O instalador não altera pacotes do sistema e instala somente o módulo Wahlap da dependência aberta, além do codec de vídeo necessário, em uma pasta privada.

```bash
python3 tools/instalar.py --game-zip "/caminho/Storm Racer G.zip" --download-dependencies
```

Adicione `~/Games/StormRacerG/jogar.sh` à biblioteca Steam como jogo externo. Deixe a compatibilidade forçada desativada: o script inicia o Proton por conta própria. Inicie pelo Steam no modo jogo.

Para fornecer dependências manualmente, use `--runtime-archive`, `--codec-archive` e `--system-profile`. URLs e SHA-256 estão no instalador e em `source/configure.py`. O instalador recusa sobrescrever uma instalação existente.

## Controles

| Controle | Função |
|---|---|
| Analógico esquerdo | Direção analógica / seleção de carro e pista |
| RT / LT | Acelerador / freio |
| A | Iniciar e confirmar; selecionar a opção no menu de pausa |
| X | Nitro |
| B | Voltar |
| Direcional | Navegação |
| Menu / Start | Abrir o menu de pausa e retomar |
| LB + RB | Menu técnico |

A configuração lê o controle virtual Xbox One Elite 2 do InputPlumber. Não usa o controle físico que já está capturado pelo serviço.

## Funcionamento

- Texto em inglês e unidades métricas já presentes nesta revisão.
- Renderização configurada em 1920×1080, janela sem bordas na tela do Ally. Os recursos gráficos e a interface mantêm a arte original.
- Jogo local; a lista de servidores de sincronização é esvaziada. Multiplayer em rede e gabinete de movimento não são parte desta integração.
- Interface de controles a 125 Hz, comunicação TCP somente em loopback.
- Avisos da versão de desenvolvimento deixam de restaurar o console sobre a partida.
- Pausa com interface própria em inglês: PAUSED, RESUME e INFINITE BOOST — YES / NO. Use o direcional para escolher e A para confirmar; B ou Menu retoma. O cheat começa em NO a cada abertura do jogo, usa a opção nativa de boost infinito e pode ser alterado durante a corrida. X continua acionando o boost.
- Enquanto o menu está aberto, o processo do jogo fica parado e seus relógios descontam o intervalo da pausa.

Veja [validação](docs/VALIDACAO.md) e [dependências](docs/DEPENDENCIAS.md).

## Artes

As artes são privadas. Para aplicá-las ao Steam, forneça `portrait.jpg`, `hero.jpg`, `landscape.jpg`, `logo.png` e `icon.png` em `artes/` e use `tools/instalar_artes.py --root ... --app-id ... --account ...`, com o Steam aberto e sua interface de depuração local disponível. Nenhuma imagem acompanha este projeto.

## Publicação

```bash
python3 tools/publicar_pacote.py --check
python3 tools/publicar_pacote.py
```

Somente os arquivos listados em `PUBLIC_FILES.txt` entram no pacote. Não inicialize Git na pasta privada que contém o jogo.
